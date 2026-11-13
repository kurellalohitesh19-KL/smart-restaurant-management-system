"""
reservation_service.py
-----------------------
Centralised business logic for reservations and table state management.

All reservation mutations should go through these helpers so that
table.status and reservation.status stay consistent everywhere.
"""
from app import db
from app.models.reservation import Reservation
from app.models.table import Table
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Availability helpers
# ---------------------------------------------------------------------------

def has_overlapping_reservation(table_id, reservation_date, start_time, end_time,
                                 exclude_reservation_id=None):
    """
    Return True if there is an active (pending/confirmed) reservation for the
    given table that overlaps the requested [start_time, end_time) window on
    reservation_date.

    'Active' means status is 'pending' or 'confirmed'.
    Two intervals [s1, e1) and [s2, e2) overlap when s1 < e2 and s2 < e1.
    """
    q = Reservation.query.filter(
        Reservation.table_id == table_id,
        Reservation.reservation_date == reservation_date,
        Reservation.status.in_(['pending', 'confirmed']),
        Reservation.start_time < end_time,
        Reservation.end_time > start_time,
    )
    if exclude_reservation_id:
        q = q.filter(Reservation.id != exclude_reservation_id)
    return q.first() is not None


def get_available_tables_for_slot(restaurant_id, reservation_date, start_time, end_time):
    """
    Return all Table objects for restaurant_id that are NOT under maintenance
    AND have no active reservation overlapping [start_time, end_time) on
    reservation_date.

    This is server-side, query-based — not derived from table.status.
    """
    # Tables that have an overlapping active reservation for this slot
    busy_table_ids = db.session.query(Reservation.table_id).filter(
        Reservation.restaurant_id == restaurant_id,
        Reservation.reservation_date == reservation_date,
        Reservation.status.in_(['pending', 'confirmed']),
        Reservation.start_time < end_time,
        Reservation.end_time > start_time,
    ).subquery()

    return Table.query.filter(
        Table.restaurant_id == restaurant_id,
        Table.status != 'maintenance',
        ~Table.id.in_(busy_table_ids),
    ).all()


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

def confirm_reservation(reservation):
    """
    Confirm a reservation and mark the table as 'reserved'.
    Commits the session.
    """
    reservation.status = 'confirmed'
    reservation.table.status = 'reserved'
    db.session.commit()


def auto_confirm_new_reservation(reservation):
    """
    Called right after a new Reservation object has been added to the session
    (but before commit).  Sets status to 'confirmed' and marks the table
    'reserved'.  The caller must call db.session.commit().
    """
    reservation.status = 'confirmed'
    reservation.table.status = 'reserved'


def cancel_reservation(reservation):
    """
    Cancel an active reservation.
    If no other active reservation holds the table, resets table.status to
    'available'.
    Commits the session.
    """
    reservation.status = 'cancelled'
    _release_table_if_free(reservation.table)
    db.session.commit()


def checkin_reservation(reservation):
    """
    Mark customer as physically seated (reservation → still 'confirmed',
    table → 'occupied').
    Commits the session.
    """
    if reservation.status != 'confirmed':
        raise ValueError('Only confirmed reservations can be checked in.')
    reservation.table.status = 'occupied'
    db.session.commit()


def checkout_reservation(reservation):
    """
    Mark dining session complete (reservation → 'completed').
    Releases the table to 'available' if no other active session holds it.
    Commits the session.
    """
    if reservation.status not in ('confirmed',):
        raise ValueError('Only confirmed reservations can be checked out.')
    reservation.status = 'completed'
    _release_table_if_free(reservation.table, just_completed_id=reservation.id)
    db.session.commit()


def release_table(table):
    """
    Explicitly release a table to 'available' if no active reservation/
    occupied session still holds it.  Used by staff "Mark Customer Left"
    action (when no reservation object is available).
    Commits the session.
    """
    _release_table_if_free(table)
    db.session.commit()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _release_table_if_free(table, just_completed_id=None):
    """
    Set table.status = 'available' only when there is no other
    pending/confirmed reservation that still needs it.
    Does NOT commit — caller is responsible.
    """
    q = Reservation.query.filter(
        Reservation.table_id == table.id,
        Reservation.status.in_(['pending', 'confirmed']),
    )
    if just_completed_id:
        q = q.filter(Reservation.id != just_completed_id)

    if not q.first():
        table.status = 'available'
