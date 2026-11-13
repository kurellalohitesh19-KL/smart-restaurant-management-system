import unittest
from datetime import datetime, date, timedelta, timezone
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem
from app.models.order import Order, OrderItem
from app.models.reservation import Reservation

class OperationsAnalyticsReceiptsTestCase(unittest.TestCase):
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
        self.admin = User(name='Super Admin', email='admin@test.com', role='super_admin')
        self.admin.set_password('pass')
        self.owner1 = User(name='Owner One', email='owner1@test.com', role='restaurant_owner')
        self.owner1.set_password('pass')
        self.owner2 = User(name='Owner Two', email='owner2@test.com', role='restaurant_owner')
        self.owner2.set_password('pass')
        self.staff1 = User(name='Staff One', email='staff1@test.com', role='restaurant_staff')
        self.staff1.set_password('pass')
        self.cust1 = User(name='Customer One', email='cust1@test.com', role='customer')
        self.cust1.set_password('pass')
        self.cust2 = User(name='Customer Two', email='cust2@test.com', role='customer')
        self.cust2.set_password('pass')

        db.session.add_all([self.admin, self.owner1, self.owner2, self.staff1, self.cust1, self.cust2])
        db.session.commit()

        # Restaurants
        self.r1 = Restaurant(name='Spice Garden', owner_id=self.owner1.id, city='Trichy', state='Tamil Nadu')
        self.r2 = Restaurant(name='Urban Bistro', owner_id=self.owner2.id, city='Trichy', state='Tamil Nadu')
        db.session.add_all([self.r1, self.r2])
        db.session.commit()

        # Staff assignment
        self.rs1 = RestaurantStaff(user_id=self.staff1.id, restaurant_id=self.r1.id, designation='Head Chef')
        db.session.add(self.rs1)

        # Tables
        self.t1 = Table(restaurant_id=self.r1.id, table_number='T1', capacity=4, status='available')
        self.t2 = Table(restaurant_id=self.r1.id, table_number='T2', capacity=2, status='available')
        db.session.add_all([self.t1, self.t2])

        # Menu
        self.cat1 = MenuCategory(restaurant_id=self.r1.id, name='Main Course')
        db.session.add(self.cat1)
        db.session.commit()

        self.m1 = MenuItem(restaurant_id=self.r1.id, category_id=self.cat1.id, name='Paneer Tikka', price=250.00, is_available=True)
        self.m2 = MenuItem(restaurant_id=self.r1.id, category_id=self.cat1.id, name='Garlic Naan', price=50.00, is_available=True)
        db.session.add_all([self.m1, self.m2])
        db.session.commit()

        # Order 1 for cust1 at r1
        self.order1 = Order(customer_id=self.cust1.id, restaurant_id=self.r1.id, table_id=self.t1.id, status='placed', total_amount=300.00)
        db.session.add(self.order1)
        db.session.flush()

        self.oi1 = OrderItem(order_id=self.order1.id, menu_item_id=self.m1.id, quantity=1, unit_price=250.00, subtotal=250.00)
        self.oi2 = OrderItem(order_id=self.order1.id, menu_item_id=self.m2.id, quantity=1, unit_price=50.00, subtotal=50.00)
        db.session.add_all([self.oi1, self.oi2])

        # Reservation at r1
        self.res1 = Reservation(
            customer_id=self.cust1.id,
            restaurant_id=self.r1.id,
            table_id=self.t1.id,
            reservation_date=date.today(),
            start_time=datetime.strptime('19:00', '%H:%M').time(),
            end_time=datetime.strptime('20:00', '%H:%M').time(),
            number_of_guests=2,
            status='confirmed'
        )
        db.session.add(self.res1)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login(self, email):
        self.client.post('/auth/logout')
        self.client.post('/auth/login', data={'email': email, 'password': 'pass'})

    # -------------------------------------------------------------
    # 1. Kitchen Display System Tests
    # -------------------------------------------------------------
    def test_staff_can_view_kitchen_display_and_advance_order(self):
        self._login('staff1@test.com')
        resp = self.client.get('/staff/kitchen')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'KDS LIVE', resp.data)
        self.assertIn(b'Paneer Tikka', resp.data)

        # Advance order: placed -> preparing
        post_resp = self.client.post(f'/staff/orders/{self.order1.id}/status', data={
            'status': 'preparing',
            'next': '/staff/kitchen'
        }, follow_redirects=True)
        self.assertEqual(post_resp.status_code, 200)
        self.assertEqual(Order.query.get(self.order1.id).status, 'preparing')

        # Advance order: preparing -> ready
        post_resp2 = self.client.post(f'/staff/orders/{self.order1.id}/status', data={
            'status': 'ready',
            'next': '/staff/kitchen'
        }, follow_redirects=True)
        self.assertEqual(post_resp2.status_code, 200)
        self.assertEqual(Order.query.get(self.order1.id).status, 'ready')

        # Advance order: ready -> served
        post_resp3 = self.client.post(f'/staff/orders/{self.order1.id}/status', data={
            'status': 'served',
            'next': '/staff/kitchen'
        }, follow_redirects=True)
        self.assertEqual(post_resp3.status_code, 200)
        self.assertEqual(Order.query.get(self.order1.id).status, 'served')

    def test_owner_can_view_kitchen_display(self):
        self._login('owner1@test.com')
        resp = self.client.get('/owner/kitchen')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'OWNER KDS', resp.data)
        self.assertIn(b'Paneer Tikka', resp.data)

    def test_customer_cannot_access_kitchen_display(self):
        self._login('cust1@test.com')
        resp_staff_kds = self.client.get('/staff/kitchen')
        self.assertEqual(resp_staff_kds.status_code, 403)
        resp_owner_kds = self.client.get('/owner/kitchen')
        self.assertEqual(resp_owner_kds.status_code, 403)

    # -------------------------------------------------------------
    # 2. Order Status API Tests
    # -------------------------------------------------------------
    def test_api_order_status_requires_auth(self):
        resp = self.client.get(f'/api/orders/{self.order1.id}/status')
        self.assertEqual(resp.status_code, 401)

    def test_api_order_status_customer_authorization(self):
        # Order belongs to cust1
        self._login('cust1@test.com')
        resp = self.client.get(f'/api/orders/{self.order1.id}/status')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['order_id'], self.order1.id)
        self.assertEqual(data['status'], 'placed')
        self.assertEqual(data['total_amount'], 300.0)

        # Another customer (cust2) should be rejected
        self._login('cust2@test.com')
        resp_cust2 = self.client.get(f'/api/orders/{self.order1.id}/status')
        self.assertEqual(resp_cust2.status_code, 403)

    def test_api_order_status_staff_and_owner_access(self):
        self._login('staff1@test.com')
        resp = self.client.get(f'/api/orders/{self.order1.id}/status')
        self.assertEqual(resp.status_code, 200)

        self._login('owner1@test.com')
        resp_owner = self.client.get(f'/api/orders/{self.order1.id}/status')
        self.assertEqual(resp_owner.status_code, 200)

        # Different owner cannot access
        self._login('owner2@test.com')
        resp_owner2 = self.client.get(f'/api/orders/{self.order1.id}/status')
        self.assertEqual(resp_owner2.status_code, 403)

    # -------------------------------------------------------------
    # 3. Digital Receipts Tests
    # -------------------------------------------------------------
    def test_customer_can_view_own_receipt_and_isolated_from_others(self):
        self._login('cust1@test.com')
        resp = self.client.get(f'/customer/orders/{self.order1.id}/receipt')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Tax Invoice & Dining Receipt', resp.data)
        self.assertIn(b'Paneer Tikka', resp.data)
        self.assertIn(b'300.00', resp.data)

        # cust2 cannot view cust1's receipt
        self._login('cust2@test.com')
        resp2 = self.client.get(f'/customer/orders/{self.order1.id}/receipt')
        self.assertEqual(resp2.status_code, 404)

    def test_staff_and_owner_can_view_receipt(self):
        self._login('staff1@test.com')
        resp = self.client.get(f'/staff/orders/{self.order1.id}/receipt')
        self.assertEqual(resp.status_code, 200)

        self._login('owner1@test.com')
        resp_owner = self.client.get(f'/owner/orders/{self.order1.id}/receipt')
        self.assertEqual(resp_owner.status_code, 200)

        self._login('admin@test.com')
        resp_admin = self.client.get(f'/admin/orders/{self.order1.id}/receipt')
        self.assertEqual(resp_admin.status_code, 200)

    # -------------------------------------------------------------
    # 4. Owner Reports & CSV Export Tests
    # -------------------------------------------------------------
    def test_owner_reports_view_and_metrics(self):
        self._login('owner1@test.com')
        resp = self.client.get('/owner/reports')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Analytics & Reports', resp.data)
        self.assertIn(b'300.00', resp.data)
        self.assertIn(b'Paneer Tikka', resp.data)

    def test_owner_csv_exports(self):
        self._login('owner1@test.com')
        
        # Export orders
        resp_orders = self.client.get('/owner/reports/export/orders')
        self.assertEqual(resp_orders.status_code, 200)
        self.assertEqual(resp_orders.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b'Order ID', resp_orders.data)
        self.assertIn(b'Customer One', resp_orders.data)

        # Export reservations
        resp_res = self.client.get('/owner/reports/export/reservations')
        self.assertEqual(resp_res.status_code, 200)
        self.assertEqual(resp_res.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b'Reservation ID', resp_res.data)

        # Export sales summary
        resp_sales = self.client.get('/owner/reports/export/sales')
        self.assertEqual(resp_sales.status_code, 200)
        self.assertEqual(resp_sales.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b'Paneer Tikka', resp_sales.data)

    # -------------------------------------------------------------
    # 5. Admin Reports & CSV Export Tests
    # -------------------------------------------------------------
    def test_admin_reports_and_csv_exports(self):
        self._login('admin@test.com')
        resp = self.client.get('/admin/reports')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Platform Analytics', resp.data)

        # Export orders
        resp_orders = self.client.get('/admin/reports/export/orders')
        self.assertEqual(resp_orders.status_code, 200)
        self.assertEqual(resp_orders.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b'Spice Garden', resp_orders.data)

        # Export reservations
        resp_res = self.client.get('/admin/reports/export/reservations')
        self.assertEqual(resp_res.status_code, 200)
        self.assertEqual(resp_res.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b'Reservation ID', resp_res.data)

    def test_customer_cannot_access_reports(self):
        self._login('cust1@test.com')
        resp_owner_rep = self.client.get('/owner/reports')
        self.assertEqual(resp_owner_rep.status_code, 403)
        resp_admin_rep = self.client.get('/admin/reports')
        self.assertEqual(resp_admin_rep.status_code, 403)

if __name__ == '__main__':
    unittest.main()
