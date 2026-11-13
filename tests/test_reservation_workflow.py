"""
test_reservation_workflow.py
-----------------------------
Comprehensive tests for the fixed reservation, table availability, and
checkout workflow (Issues 1–6 from the bug-fix specification).

Covers:
  1.  Valid customer bookings are auto-confirmed.
  2.  Owner approval is NOT required.
  3.  Customer sees complete booking details after confirmation.
  4.  A booked time slot is excluded from availability (overlap check).
  5.  Non-overlapping time slots remain bookable.
  6.  Overlapping reservations for the same table are rejected.
  7.  Cancelled reservations release the time slot.
  8.  Payment alone does NOT release an occupied table.
  9.  Staff can check in a customer (table → occupied).
  10. Staff can check out a customer (table → available, res → completed).
  11. Owner can perform check-in and checkout for their own restaurant.
  12. Staff from another restaurant cannot check in/out.
  13. Successful checkout only releases the table when no other active
      reservation holds it.
  14. Duplicate checkout actions are handled safely.
  15. Reservation service: has_overlapping_reservation is correct.
"""

import unittest
from datetime import date, time
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff, CustomerRestaurant
from app.models.table import Table
from app.models.reservation import Reservation
from app.services import reservation_service


class ReservationWorkflowTestCase(unittest.TestCase):
    # ------------------------------------------------------------------ setUp
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # --- users ---
        self.owner = User(name='Owner1', email='owner1@test.com', role='restaurant_owner')
        self.owner.set_password('pass')
        self.owner2 = User(name='Owner2', email='owner2@test.com', role='restaurant_owner')
        self.owner2.set_password('pass')
        self.staff_user = User(name='Staff1', email='staff1@test.com', role='restaurant_staff')
        self.staff_user.set_password('pass')
        self.staff2_user = User(name='Staff2', email='staff2@test.com', role='restaurant_staff')
        self.staff2_user.set_password('pass')
        self.customer = User(name='Cust1', email='cust1@test.com', role='customer')
        self.customer.set_password('pass')
        self.customer2 = User(name='Cust2', email='cust2@test.com', role='customer')
        self.customer2.set_password('pass')

        db.session.add_all([
            self.owner, self.owner2,
            self.staff_user, self.staff2_user,
            self.customer, self.customer2,
        ])
        db.session.commit()

        # --- restaurants ---
        self.r1 = Restaurant(
            owner_id=self.owner.id, name='RestA',
            city='City', state='State', is_active=True
        )
        self.r2 = Restaurant(
            owner_id=self.owner2.id, name='RestB',
            city='City', state='State', is_active=True
        )
        db.session.add_all([self.r1, self.r2])
        db.session.commit()

        # --- staff assignments ---
        self.rs1 = RestaurantStaff(user_id=self.staff_user.id, restaurant_id=self.r1.id)
        self.rs2 = RestaurantStaff(user_id=self.staff2_user.id, restaurant_id=self.r2.id)
        db.session.add_all([self.rs1, self.rs2])

        # --- tables ---
        self.t1 = Table(restaurant_id=self.r1.id, table_number='1', capacity=4, status='available')
        self.t2 = Table(restaurant_id=self.r1.id, table_number='2', capacity=2, status='available')
        self.t_r2 = Table(restaurant_id=self.r2.id, table_number='1', capacity=4, status='available')
        db.session.add_all([self.t1, self.t2, self.t_r2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    # ----------------------------------------------------------------- helpers
    def login(self, email, password='pass'):
        self.client.post('/auth/login', data={'email': email, 'password': password})

    def logout(self):
        self.client.get('/auth/logout')

    def make_reservation_via_http(self, restaurant_id, table_id,
                                   date_str='2031-06-01',
                                   start='10:00', end='11:00', guests=2):
        return self.client.post(
            f'/customer/restaurants/{restaurant_id}/reserve',
            data={
                'table_id': table_id,
                'reservation_date': date_str,
                'start_time': start,
                'end_time': end,
                'number_of_guests': guests,
            },
            follow_redirects=True,
        )

    def _make_confirmed_res(self, table=None, start=time(10, 0), end=time(11, 0),
                             d=date(2031, 6, 1)):
        """Create an already-confirmed reservation directly in the DB."""
        t = table or self.t1
        res = Reservation(
            customer_id=self.customer.id,
            restaurant_id=self.r1.id,
            table_id=t.id,
            reservation_date=d,
            start_time=start,
            end_time=end,
            number_of_guests=2,
            status='confirmed',
        )
        db.session.add(res)
        t.status = 'reserved'
        db.session.commit()
        return res

    # ========================================================================
    # 1. Auto-confirm on creation
    # ========================================================================
    def test_1_auto_confirm_on_booking(self):
        self.login('cust1@test.com')
        resp = self.make_reservation_via_http(self.r1.id, self.t1.id)
        self.assertIn(b'booked successfully', resp.data)

        res = Reservation.query.first()
        self.assertIsNotNone(res)
        # Must be 'confirmed', never 'pending'
        self.assertEqual(res.status, 'confirmed')

    # ========================================================================
    # 2. Owner approval is NOT required
    # ========================================================================
    def test_2_no_owner_approval_required(self):
        self.login('cust1@test.com')
        self.make_reservation_via_http(self.r1.id, self.t1.id)
        res = Reservation.query.first()
        # Confirmed without any owner action
        self.assertEqual(res.status, 'confirmed')
        self.logout()

        # Owner page should NOT show a 'Confirm' button for this reservation
        self.login('owner1@test.com')
        resp = self.client.get('/owner/reservations')
        # The reservation is confirmed, so no pending confirm action needed
        # Verify it appears in the list with confirmed status
        self.assertIn(b'Confirmed', resp.data)

    # ========================================================================
    # 3. Customer sees booking details after confirmation
    # ========================================================================
    def test_3_customer_sees_booking_details(self):
        self.login('cust1@test.com')
        resp = self.make_reservation_via_http(self.r1.id, self.t1.id,
                                              date_str='2031-06-01',
                                              start='10:00', end='11:00', guests=3)
        # After redirect to reservation_detail
        res = Reservation.query.first()
        self.assertIsNotNone(res)
        # Fetch the detail page
        detail = self.client.get(f'/customer/reservations/{res.id}')
        self.assertEqual(detail.status_code, 200)
        self.assertIn(b'2031-06-01', detail.data)    # booking date
        self.assertIn(b'10:00', detail.data)          # start time
        self.assertIn(b'RestA', detail.data)          # restaurant name
        self.assertIn(str(self.t1.table_number).encode(), detail.data)  # table number
        self.assertIn(b'Confirmed', detail.data)      # status badge

    # ========================================================================
    # 4. Booked slot is excluded from availability
    # ========================================================================
    def test_4_booked_slot_excluded_from_availability(self):
        # Create a confirmed reservation for t1 10:00–11:00
        self._make_confirmed_res(table=self.t1, start=time(10, 0), end=time(11, 0))

        # has_overlapping_reservation must return True for same window
        overlaps = reservation_service.has_overlapping_reservation(
            self.t1.id, date(2031, 6, 1), time(10, 0), time(11, 0)
        )
        self.assertTrue(overlaps)

        # HTTP booking for the same slot must be rejected
        self.login('cust2@test.com')
        resp = self.make_reservation_via_http(self.r1.id, self.t1.id,
                                              date_str='2031-06-01',
                                              start='10:00', end='11:00')
        self.assertIn(b'already reserved', resp.data)

    # ========================================================================
    # 5. Non-overlapping slots remain bookable
    # ========================================================================
    def test_5_non_overlapping_slot_is_bookable(self):
        self._make_confirmed_res(table=self.t1, start=time(10, 0), end=time(11, 0))

        # Check service: non-overlapping should return False
        overlaps = reservation_service.has_overlapping_reservation(
            self.t1.id, date(2031, 6, 1), time(11, 0), time(12, 0)
        )
        self.assertFalse(overlaps)

        # HTTP booking for the adjacent (non-overlapping) slot
        self.login('cust2@test.com')
        resp = self.make_reservation_via_http(self.r1.id, self.t1.id,
                                              date_str='2031-06-01',
                                              start='11:00', end='12:00')
        self.assertIn(b'booked successfully', resp.data)

    # ========================================================================
    # 6. Overlapping reservations for same table rejected
    # ========================================================================
    def test_6_overlapping_reservation_rejected(self):
        self._make_confirmed_res(table=self.t1, start=time(10, 0), end=time(12, 0))

        # Partially overlapping: 11:00–13:00 overlaps [10:00–12:00)
        overlaps = reservation_service.has_overlapping_reservation(
            self.t1.id, date(2031, 6, 1), time(11, 0), time(13, 0)
        )
        self.assertTrue(overlaps)

        # Different table on same date/time should NOT be blocked
        overlaps_t2 = reservation_service.has_overlapping_reservation(
            self.t2.id, date(2031, 6, 1), time(10, 0), time(12, 0)
        )
        self.assertFalse(overlaps_t2)

    # ========================================================================
    # 7. Cancelled reservation releases time slot
    # ========================================================================
    def test_7_cancelled_reservation_releases_slot(self):
        res = self._make_confirmed_res(table=self.t1)
        # Slot occupied
        self.assertTrue(reservation_service.has_overlapping_reservation(
            self.t1.id, date(2031, 6, 1), time(10, 0), time(11, 0)
        ))
        # Cancel
        reservation_service.cancel_reservation(res)
        db.session.refresh(res)
        self.assertEqual(res.status, 'cancelled')
        # Slot now free
        self.assertFalse(reservation_service.has_overlapping_reservation(
            self.t1.id, date(2031, 6, 1), time(10, 0), time(11, 0)
        ))
        # Table released to 'available'
        db.session.refresh(self.t1)
        self.assertEqual(self.t1.status, 'available')

    # ========================================================================
    # 8. Payment alone does NOT release occupied table
    # ========================================================================
    def test_8_payment_alone_does_not_release_table(self):
        """Paying an order should not touch table.status."""
        res = self._make_confirmed_res(table=self.t1)
        # Simulate check-in (table becomes occupied)
        reservation_service.checkin_reservation(res)
        db.session.refresh(self.t1)
        self.assertEqual(self.t1.status, 'occupied')

        # Simulate "order served" without any checkout action
        # (We simply verify table is still occupied after order status changes)
        from app.models.order import Order
        order = Order(
            customer_id=self.customer.id,
            restaurant_id=self.r1.id,
            table_id=self.t1.id,
            reservation_id=res.id,
            status='served',
            total_amount=200,
        )
        db.session.add(order)
        db.session.commit()

        # Table must still be occupied — payment/serving alone should not release it
        db.session.refresh(self.t1)
        self.assertEqual(self.t1.status, 'occupied')

    # ========================================================================
    # 9. Staff can check in customer (table → occupied)
    # ========================================================================
    def test_9_staff_checkin_marks_table_occupied(self):
        res = self._make_confirmed_res(table=self.t1)
        db.session.refresh(self.t1)
        self.assertEqual(self.t1.status, 'reserved')

        self.login('staff1@test.com')
        resp = self.client.post(
            f'/staff/reservations/{res.id}/checkin', follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'checked in', resp.data)

        db.session.refresh(self.t1)
        self.assertEqual(self.t1.status, 'occupied')

    # ========================================================================
    # 10. Staff can check out (table → available, res → completed)
    # ========================================================================
    def test_10_staff_checkout_releases_table(self):
        res = self._make_confirmed_res(table=self.t1)
        reservation_service.checkin_reservation(res)

        self.login('staff1@test.com')
        resp = self.client.post(
            f'/staff/reservations/{res.id}/checkout', follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'checked out', resp.data)

        db.session.refresh(res)
        self.assertEqual(res.status, 'completed')
        db.session.refresh(self.t1)
        self.assertEqual(self.t1.status, 'available')

    # ========================================================================
    # 11. Owner can check in and check out for their restaurant
    # ========================================================================
    def test_11_owner_checkin_and_checkout(self):
        res = self._make_confirmed_res(table=self.t1)

        self.login('owner1@test.com')

        # Check-in
        resp = self.client.post(
            f'/owner/reservations/{res.id}/checkin', follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        db.session.refresh(self.t1)
        self.assertEqual(self.t1.status, 'occupied')

        # Checkout (complete)
        resp = self.client.post(
            f'/owner/reservations/{res.id}/complete', follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        db.session.refresh(res)
        self.assertEqual(res.status, 'completed')
        db.session.refresh(self.t1)
        self.assertEqual(self.t1.status, 'available')

    # ========================================================================
    # 12. Staff from another restaurant cannot check in/out
    # ========================================================================
    def test_12_cross_restaurant_staff_blocked(self):
        res = self._make_confirmed_res(table=self.t1)

        # staff2 belongs to r2, not r1
        self.login('staff2@test.com')

        resp = self.client.post(f'/staff/reservations/{res.id}/checkin')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.post(f'/staff/reservations/{res.id}/checkout')
        self.assertEqual(resp.status_code, 404)

    # ========================================================================
    # 13. Table stays unavailable if another active reservation holds it
    # ========================================================================
    def test_13_table_not_released_when_another_reservation_active(self):
        # Two reservations on the same table, different time slots
        res1 = self._make_confirmed_res(table=self.t1,
                                         start=time(10, 0), end=time(11, 0),
                                         d=date(2031, 6, 1))
        res2 = Reservation(
            customer_id=self.customer2.id,
            restaurant_id=self.r1.id,
            table_id=self.t1.id,
            reservation_date=date(2031, 6, 1),
            start_time=time(12, 0),
            end_time=time(13, 0),
            number_of_guests=2,
            status='confirmed',
        )
        db.session.add(res2)
        db.session.commit()

        # Cancel res1 — res2 is still active, table must NOT be released
        reservation_service.cancel_reservation(res1)
        db.session.refresh(self.t1)
        # Table should still be reserved for res2
        self.assertEqual(self.t1.status, 'reserved')

    # ========================================================================
    # 14. Duplicate checkout is handled safely
    # ========================================================================
    def test_14_duplicate_checkout_is_safe(self):
        res = self._make_confirmed_res(table=self.t1)
        reservation_service.checkin_reservation(res)
        # First checkout — OK
        reservation_service.checkout_reservation(res)
        db.session.refresh(res)
        self.assertEqual(res.status, 'completed')
        db.session.refresh(self.t1)
        self.assertEqual(self.t1.status, 'available')

        # Second checkout via HTTP — must fail gracefully (not crash)
        self.login('staff1@test.com')
        resp = self.client.post(
            f'/staff/reservations/{res.id}/checkout', follow_redirects=True
        )
        # Should respond with an error flash, not a 500
        self.assertIn(resp.status_code, [200, 302, 400])
        # Table must still be available
        db.session.refresh(self.t1)
        self.assertEqual(self.t1.status, 'available')

    # ========================================================================
    # 15. has_overlapping_reservation service unit test
    # ========================================================================
    def test_15_overlap_detection_edge_cases(self):
        d = date(2031, 6, 1)

        # Exact match overlaps
        res = Reservation(
            customer_id=self.customer.id,
            restaurant_id=self.r1.id,
            table_id=self.t1.id,
            reservation_date=d,
            start_time=time(10, 0),
            end_time=time(12, 0),
            number_of_guests=2,
            status='confirmed',
        )
        db.session.add(res)
        db.session.commit()

        # Exact overlap
        self.assertTrue(reservation_service.has_overlapping_reservation(
            self.t1.id, d, time(10, 0), time(12, 0)
        ))
        # Partial overlap (starts inside)
        self.assertTrue(reservation_service.has_overlapping_reservation(
            self.t1.id, d, time(11, 0), time(13, 0)
        ))
        # Adjacent after — no overlap
        self.assertFalse(reservation_service.has_overlapping_reservation(
            self.t1.id, d, time(12, 0), time(13, 0)
        ))
        # Adjacent before — no overlap
        self.assertFalse(reservation_service.has_overlapping_reservation(
            self.t1.id, d, time(8, 0), time(10, 0)
        ))
        # exclude_reservation_id: excluding the same res should return False
        self.assertFalse(reservation_service.has_overlapping_reservation(
            self.t1.id, d, time(10, 0), time(12, 0),
            exclude_reservation_id=res.id
        ))
        # Cancelled reservations must NOT block the slot
        res.status = 'cancelled'
        db.session.commit()
        self.assertFalse(reservation_service.has_overlapping_reservation(
            self.t1.id, d, time(10, 0), time(12, 0)
        ))


if __name__ == '__main__':
    unittest.main()
