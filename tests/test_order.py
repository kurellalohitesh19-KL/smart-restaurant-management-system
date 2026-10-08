import unittest
from decimal import Decimal
from datetime import datetime, timezone
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff, CustomerRestaurant
from app.models.menu import MenuCategory, MenuItem
from app.models.order import Order, OrderItem
from flask import session

class OrderTestCase(unittest.TestCase):
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
        self.owner1 = User(name='Owner 1', email='owner1@test.com', role='restaurant_owner')
        self.owner1.set_password('pass')
        self.owner2 = User(name='Owner 2', email='owner2@test.com', role='restaurant_owner')
        self.owner2.set_password('pass')
        self.staff1 = User(name='Staff 1', email='staff1@test.com', role='restaurant_staff')
        self.staff1.set_password('pass')
        self.customer1 = User(name='Customer 1', email='customer1@test.com', role='customer')
        self.customer1.set_password('pass')
        self.customer2 = User(name='Customer 2', email='customer2@test.com', role='customer')
        self.customer2.set_password('pass')

        db.session.add_all([self.owner1, self.owner2, self.staff1, self.customer1, self.customer2])
        db.session.commit()

        # Restaurants
        self.r1 = Restaurant(owner_id=self.owner1.id, name='Rest 1', city='City 1', state='State 1', is_active=True)
        self.r2 = Restaurant(owner_id=self.owner2.id, name='Rest 2', city='City 2', state='State 2', is_active=True)
        self.r_inactive = Restaurant(owner_id=self.owner1.id, name='Rest Inactive', city='City 3', state='State 3', is_active=False)
        db.session.add_all([self.r1, self.r2, self.r_inactive])
        db.session.commit()

        # Staff assignment
        self.rs1 = RestaurantStaff(user_id=self.staff1.id, restaurant_id=self.r1.id)
        db.session.add(self.rs1)
        db.session.commit()

        # Menus
        self.c1 = MenuCategory(restaurant_id=self.r1.id, name='Cat 1', is_active=True)
        self.c2 = MenuCategory(restaurant_id=self.r2.id, name='Cat 2', is_active=True)
        self.c_inactive = MenuCategory(restaurant_id=self.r_inactive.id, name='Cat Inactive', is_active=True)
        db.session.add_all([self.c1, self.c2, self.c_inactive])
        db.session.commit()

        self.m1 = MenuItem(restaurant_id=self.r1.id, category_id=self.c1.id, name='Item 1', price=Decimal('100.00'), is_available=True)
        self.m1_unavail = MenuItem(restaurant_id=self.r1.id, category_id=self.c1.id, name='Item 1 Unavail', price=Decimal('150.00'), is_available=False)
        self.m2 = MenuItem(restaurant_id=self.r2.id, category_id=self.c2.id, name='Item 2', price=Decimal('200.00'), is_available=True)
        self.m_inactive = MenuItem(restaurant_id=self.r_inactive.id, category_id=self.c_inactive.id, name='Item Inactive', price=Decimal('50.00'), is_available=True)
        db.session.add_all([self.m1, self.m1_unavail, self.m2, self.m_inactive])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password='pass'):
        self.client.post('/auth/login', data={'email': email, 'password': password})

    def logout(self):
        self.client.get('/auth/logout')

    def test_unauthenticated_blocked(self):
        resp = self.client.get('/customer/cart')
        self.assertEqual(resp.status_code, 302)

    def test_customer_can_add_available_item(self):
        self.login('customer1@test.com')
        resp = self.client.post('/customer/cart/add', data={'menu_item_id': self.m1.id}, follow_redirects=True)
        self.assertIn(b'Item added to cart.', resp.data)
        
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['cart'][str(self.m1.id)], 1)
            self.assertEqual(sess['cart_restaurant_id'], self.r1.id)

    def test_customer_cannot_add_unavailable_item(self):
        self.login('customer1@test.com')
        resp = self.client.post('/customer/cart/add', data={'menu_item_id': self.m1_unavail.id}, follow_redirects=True)
        self.assertIn(b'Menu item not found or unavailable.', resp.data)

    def test_customer_cannot_mix_restaurants(self):
        self.login('customer1@test.com')
        self.client.post('/customer/cart/add', data={'menu_item_id': self.m1.id})
        
        resp = self.client.post('/customer/cart/add', data={'menu_item_id': self.m2.id}, follow_redirects=True)
        self.assertIn(b'You can only order from one restaurant at a time', resp.data)
        
        with self.client.session_transaction() as sess:
            self.assertNotIn(str(self.m2.id), sess['cart'])

    def test_cart_quantity_updates(self):
        self.login('customer1@test.com')
        self.client.post('/customer/cart/add', data={'menu_item_id': self.m1.id})
        
        resp = self.client.post('/customer/cart/update', data={'menu_item_id': self.m1.id, 'quantity': 3}, follow_redirects=True)
        self.assertIn(b'Cart updated.', resp.data)
        
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['cart'][str(self.m1.id)], 3)

    def test_invalid_quantity_rejected(self):
        self.login('customer1@test.com')
        self.client.post('/customer/cart/add', data={'menu_item_id': self.m1.id})
        resp = self.client.post('/customer/cart/update', data={'menu_item_id': self.m1.id, 'quantity': -1}, follow_redirects=True)
        self.assertIn(b'Invalid quantity.', resp.data)

    def test_cart_item_removal(self):
        self.login('customer1@test.com')
        self.client.post('/customer/cart/add', data={'menu_item_id': self.m1.id})
        resp = self.client.post('/customer/cart/remove', data={'menu_item_id': self.m1.id}, follow_redirects=True)
        self.assertIn(b'Item removed from cart.', resp.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn(str(self.m1.id), sess.get('cart', {}))
            self.assertIsNone(sess.get('cart_restaurant_id'))

    def test_order_creation_and_totals(self):
        self.login('customer1@test.com')
        self.client.post('/customer/cart/add', data={'menu_item_id': self.m1.id})
        self.client.post('/customer/cart/update', data={'menu_item_id': self.m1.id, 'quantity': 2})
        
        resp = self.client.post('/customer/order/place', follow_redirects=True)
        self.assertIn(b'Order placed successfully.', resp.data)
        
        order = Order.query.filter_by(customer_id=self.customer1.id).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'placed')
        self.assertEqual(order.total_amount, Decimal('200.00')) # 2 * 100
        self.assertEqual(len(order.items), 1)
        self.assertEqual(order.items[0].subtotal, Decimal('200.00'))
        self.assertEqual(order.items[0].unit_price, Decimal('100.00'))
        self.assertEqual(order.items[0].quantity, 2)
        
        # Check CustomerRestaurant creation
        cr = CustomerRestaurant.query.filter_by(customer_id=self.customer1.id, restaurant_id=self.r1.id).first()
        self.assertIsNotNone(cr)
        
        # Verify cart cleared
        with self.client.session_transaction() as sess:
            self.assertNotIn('cart', sess)
            self.assertNotIn('cart_restaurant_id', sess)

    def test_inactive_restaurant_blocked(self):
        self.login('customer1@test.com')
        resp = self.client.post('/customer/cart/add', data={'menu_item_id': self.m_inactive.id}, follow_redirects=True)
        self.assertIn(b'Restaurant is inactive.', resp.data)

    def test_historical_price_preservation(self):
        self.login('customer1@test.com')
        self.client.post('/customer/cart/add', data={'menu_item_id': self.m1.id})
        self.client.post('/customer/order/place')
        
        # Change price
        item = MenuItem.query.get(self.m1.id)
        item.price = Decimal('150.00')
        db.session.commit()
        
        order = Order.query.filter_by(customer_id=self.customer1.id).first()
        self.assertEqual(order.items[0].unit_price, Decimal('100.00'))
        self.assertEqual(order.total_amount, Decimal('100.00'))

    def test_customer_isolation(self):
        order = Order(customer_id=self.customer1.id, restaurant_id=self.r1.id, total_amount=100.00)
        db.session.add(order)
        db.session.commit()
        
        self.login('customer2@test.com')
        resp = self.client.get(f'/customer/orders/{order.id}')
        self.assertEqual(resp.status_code, 404)
        
        self.logout()
        self.login('customer1@test.com')
        resp = self.client.get(f'/customer/orders/{order.id}')
        self.assertEqual(resp.status_code, 200)

    def test_owner_isolation_and_status(self):
        order = Order(customer_id=self.customer1.id, restaurant_id=self.r1.id, total_amount=100.00)
        db.session.add(order)
        db.session.commit()
        
        self.login('owner2@test.com')
        resp = self.client.get(f'/owner/orders/{order.id}')
        self.assertEqual(resp.status_code, 404)
        
        self.logout()
        self.login('owner1@test.com')
        resp = self.client.get(f'/owner/orders/{order.id}')
        self.assertEqual(resp.status_code, 200)
        
        # Valid transition
        resp = self.client.post(f'/owner/orders/{order.id}/status', data={'status': 'confirmed'}, follow_redirects=True)
        self.assertIn(b'Order status updated', resp.data)
        db.session.refresh(order)
        self.assertEqual(order.status, 'confirmed')
        
        # Invalid transition
        resp = self.client.post(f'/owner/orders/{order.id}/status', data={'status': 'served'}, follow_redirects=True)
        self.assertIn(b'Invalid status transition', resp.data)
        db.session.refresh(order)
        self.assertEqual(order.status, 'confirmed')

    def test_staff_isolation_and_status(self):
        order = Order(customer_id=self.customer1.id, restaurant_id=self.r1.id, total_amount=100.00, status='confirmed')
        db.session.add(order)
        db.session.commit()
        
        # Staff 1 belongs to R1
        self.login('staff1@test.com')
        resp = self.client.get(f'/staff/orders/{order.id}')
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.post(f'/staff/orders/{order.id}/status', data={'status': 'preparing'}, follow_redirects=True)
        db.session.refresh(order)
        self.assertEqual(order.status, 'preparing')

    def test_customer_can_add_item_to_placed_order(self):
        order = Order(customer_id=self.customer1.id, restaurant_id=self.r1.id, status='placed', total_amount=100.00)
        oi = OrderItem(order=order, menu_item_id=self.m1.id, quantity=1, unit_price=100.00, subtotal=100.00)
        db.session.add_all([order, oi])
        db.session.commit()
        
        self.login('customer1@test.com')
        # Add another item
        m_new = MenuItem(restaurant_id=self.r1.id, category_id=self.c1.id, name='New Item', price=Decimal('50.00'), is_available=True)
        db.session.add(m_new)
        db.session.commit()
        
        resp = self.client.post(f'/customer/orders/{order.id}/add-item', data={'menu_item_id': m_new.id, 'quantity': 2}, follow_redirects=True)
        self.assertIn(b'Item added to order.', resp.data)
        
        db.session.refresh(order)
        self.assertEqual(len(order.items), 2)
        self.assertEqual(order.total_amount, Decimal('200.00'))

    def test_customer_cannot_add_other_restaurant_item(self):
        order = Order(customer_id=self.customer1.id, restaurant_id=self.r1.id, status='placed', total_amount=100.00)
        db.session.add(order)
        db.session.commit()
        
        self.login('customer1@test.com')
        resp = self.client.post(f'/customer/orders/{order.id}/add-item', data={'menu_item_id': self.m2.id, 'quantity': 1}, follow_redirects=True)
        self.assertIn(b'Menu item not found or does not belong to this restaurant.', resp.data)

    def test_customer_can_update_quantity(self):
        order = Order(customer_id=self.customer1.id, restaurant_id=self.r1.id, status='placed', total_amount=100.00)
        oi = OrderItem(order=order, menu_item_id=self.m1.id, quantity=1, unit_price=100.00, subtotal=100.00)
        db.session.add_all([order, oi])
        db.session.commit()
        
        self.login('customer1@test.com')
        resp = self.client.post(f'/customer/orders/{order.id}/update-item', data={'order_item_id': oi.id, 'quantity': 3}, follow_redirects=True)
        self.assertIn(b'Order item updated.', resp.data)
        
        db.session.refresh(order)
        db.session.refresh(oi)
        self.assertEqual(oi.quantity, 3)
        self.assertEqual(oi.subtotal, Decimal('300.00'))
        self.assertEqual(order.total_amount, Decimal('300.00'))

    def test_customer_can_remove_item(self):
        order = Order(customer_id=self.customer1.id, restaurant_id=self.r1.id, status='placed', total_amount=300.00)
        oi1 = OrderItem(order=order, menu_item_id=self.m1.id, quantity=1, unit_price=100.00, subtotal=100.00)
        m_new = MenuItem(restaurant_id=self.r1.id, category_id=self.c1.id, name='New Item', price=Decimal('200.00'), is_available=True)
        db.session.add(m_new)
        db.session.commit()
        oi2 = OrderItem(order=order, menu_item_id=m_new.id, quantity=1, unit_price=200.00, subtotal=200.00)
        db.session.add_all([order, oi1, oi2])
        db.session.commit()
        
        self.login('customer1@test.com')
        resp = self.client.post(f'/customer/orders/{order.id}/remove-item', data={'order_item_id': oi1.id}, follow_redirects=True)
        self.assertIn(b'Order item removed.', resp.data)
        
        db.session.refresh(order)
        self.assertEqual(len(order.items), 1)
        self.assertEqual(order.total_amount, Decimal('200.00'))

    def test_customer_cannot_remove_last_item(self):
        order = Order(customer_id=self.customer1.id, restaurant_id=self.r1.id, status='placed', total_amount=100.00)
        oi = OrderItem(order=order, menu_item_id=self.m1.id, quantity=1, unit_price=100.00, subtotal=100.00)
        db.session.add_all([order, oi])
        db.session.commit()
        
        self.login('customer1@test.com')
        resp = self.client.post(f'/customer/orders/{order.id}/remove-item', data={'order_item_id': oi.id}, follow_redirects=True)
        self.assertIn(b'Cannot remove the last item.', resp.data)

    def test_customer_confirm_final_order(self):
        order = Order(customer_id=self.customer1.id, restaurant_id=self.r1.id, status='placed', total_amount=100.00)
        db.session.add(order)
        db.session.commit()
        
        self.login('customer1@test.com')
        resp = self.client.post(f'/customer/orders/{order.id}/confirm', follow_redirects=True)
        self.assertIn(b'Final order confirmed', resp.data)
        
        db.session.refresh(order)
        self.assertTrue(order.is_customer_confirmed)
        
        # After confirming, cannot modify
        resp = self.client.post(f'/customer/orders/{order.id}/add-item', data={'menu_item_id': self.m1.id, 'quantity': 1}, follow_redirects=True)
        self.assertIn(b'Order is locked', resp.data)

    def test_cannot_modify_locked_order(self):
        order = Order(customer_id=self.customer1.id, restaurant_id=self.r1.id, status='preparing', total_amount=100.00)
        db.session.add(order)
        db.session.commit()
        
        self.login('customer1@test.com')
        resp = self.client.post(f'/customer/orders/{order.id}/add-item', data={'menu_item_id': self.m1.id, 'quantity': 1}, follow_redirects=True)
        self.assertIn(b'Order is locked', resp.data)

if __name__ == '__main__':
    unittest.main()
