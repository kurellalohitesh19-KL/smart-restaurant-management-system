from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils import role_required
from app import db
from app.models.restaurant import RestaurantStaff
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem
from app.models.reservation import Reservation
from app.models.order import Order, OrderItem
from app.services import reservation_service
from datetime import datetime

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/dashboard')
@role_required('restaurant_staff')
def dashboard():
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        return {'message': 'Staff record not found. Please contact your restaurant owner.'}
        
    restaurant = staff_record.restaurant
    
    # Tables
    tables = Table.query.filter_by(restaurant_id=restaurant.id).all()
    table_stats = {
        'available': sum(1 for t in tables if t.status == 'available'),
        'occupied': sum(1 for t in tables if t.status == 'occupied'),
        'reserved': sum(1 for t in tables if t.status == 'reserved'),
        'maintenance': sum(1 for t in tables if t.status == 'maintenance')
    }

    # Reservations
    today = datetime.now().date()
    reservations = Reservation.query.filter_by(restaurant_id=restaurant.id).all()
    res_stats = {
        'today': sum(1 for r in reservations if r.reservation_date == today),
        'pending': sum(1 for r in reservations if r.status == 'pending'),
        'confirmed': sum(1 for r in reservations if r.status == 'confirmed')
    }

    # Orders
    orders = Order.query.filter_by(restaurant_id=restaurant.id).all()
    order_stats = {
        'placed': sum(1 for o in orders if o.status == 'placed'),
        'confirmed': sum(1 for o in orders if o.status == 'confirmed'),
        'preparing': sum(1 for o in orders if o.status == 'preparing'),
        'ready': sum(1 for o in orders if o.status == 'ready')
    }

    active_orders = Order.query.filter_by(restaurant_id=restaurant.id).filter(
        Order.status.in_(['placed', 'confirmed', 'preparing', 'ready'])
    ).order_by(Order.created_at.desc()).all()

    today_reservations = Reservation.query.filter_by(restaurant_id=restaurant.id).filter(
        Reservation.reservation_date == today
    ).order_by(Reservation.start_time).all()

    return render_template('staff/dashboard.html', 
                           staff_record=staff_record, 
                           restaurant=restaurant,
                           tables=tables,
                           table_stats=table_stats,
                           res_stats=res_stats,
                           order_stats=order_stats,
                           active_orders=active_orders,
                           today_reservations=today_reservations)

# --- Table Management ---

@staff_bp.route('/tables')
@role_required('restaurant_staff')
def list_tables():
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)
        
    tables = Table.query.filter_by(restaurant_id=staff_record.restaurant_id).all()
    return render_template('staff/tables.html', tables=tables, restaurant=staff_record.restaurant)

@staff_bp.route('/tables/<int:table_id>/status', methods=['POST'])
@role_required('restaurant_staff')
def update_table_status(table_id):
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)
        
    table = Table.query.filter_by(id=table_id, restaurant_id=staff_record.restaurant_id).first_or_404()
    
    status = request.form.get('status')
    valid_statuses = ['available', 'occupied', 'maintenance']
    
    if status not in valid_statuses:
        flash("Invalid status selected. Staff can only set to available, occupied, or maintenance.", "danger")
        return redirect(url_for('staff.list_tables'))
        
    table.status = status
    db.session.commit()
    flash("Table status updated successfully.", "success")
    return redirect(url_for('staff.list_tables'))

# --- Menu Management ---

@staff_bp.route('/menu')
@role_required('restaurant_staff')
def view_menu():
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)
        
    categories = MenuCategory.query.filter_by(restaurant_id=staff_record.restaurant_id).all()
    return render_template('staff/menu.html', categories=categories, restaurant=staff_record.restaurant)

# --- Reservation Management ---

@staff_bp.route('/reservations')
@role_required('restaurant_staff')
def list_reservations():
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        flash("You must be assigned to a restaurant to manage reservations.", "warning")
        return redirect(url_for('staff.dashboard'))
        
    reservations = Reservation.query.filter_by(restaurant_id=staff_record.restaurant_id).order_by(Reservation.reservation_date.desc(), Reservation.start_time.desc()).all()
    return render_template('staff/reservations.html', reservations=reservations, restaurant=staff_record.restaurant)

@staff_bp.route('/reservations/<int:reservation_id>/confirm', methods=['POST'])
@role_required('restaurant_staff')
def confirm_reservation(reservation_id):
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)

    reservation = Reservation.query.filter_by(id=reservation_id, restaurant_id=staff_record.restaurant_id).first_or_404()
    if reservation.status == 'pending':
        reservation_service.confirm_reservation(reservation)
        flash('Reservation confirmed successfully.', 'success')
    else:
        flash('Only pending reservations can be confirmed.', 'error')
    return redirect(url_for('staff.list_reservations'))

@staff_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@role_required('restaurant_staff')
def cancel_reservation(reservation_id):
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)

    reservation = Reservation.query.filter_by(id=reservation_id, restaurant_id=staff_record.restaurant_id).first_or_404()
    if reservation.status in ['pending', 'confirmed']:
        reservation_service.cancel_reservation(reservation)
        flash('Reservation cancelled successfully.', 'success')
    else:
        flash('Reservation cannot be cancelled.', 'error')
    return redirect(url_for('staff.list_reservations'))


@staff_bp.route('/reservations/<int:reservation_id>/checkin', methods=['POST'])
@role_required('restaurant_staff')
def checkin_reservation(reservation_id):
    """Mark customer as physically seated — table becomes 'occupied'."""
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)

    reservation = Reservation.query.filter_by(id=reservation_id, restaurant_id=staff_record.restaurant_id).first_or_404()
    if reservation.status == 'confirmed':
        try:
            reservation_service.checkin_reservation(reservation)
            flash('Customer checked in — table marked as occupied.', 'success')
        except ValueError as e:
            flash(str(e), 'danger')
    else:
        flash('Only confirmed reservations can be checked in.', 'error')
    return redirect(url_for('staff.list_reservations'))


@staff_bp.route('/reservations/<int:reservation_id>/checkout', methods=['POST'])
@role_required('restaurant_staff')
def checkout_reservation(reservation_id):
    """Mark dining complete and release the table."""
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)

    reservation = Reservation.query.filter_by(id=reservation_id, restaurant_id=staff_record.restaurant_id).first_or_404()
    if reservation.status == 'confirmed':
        try:
            reservation_service.checkout_reservation(reservation)
            flash('Customer checked out — table is now available.', 'success')
        except ValueError as e:
            flash(str(e), 'danger')
    else:
        flash('Only confirmed reservations can be checked out.', 'error')
    return redirect(url_for('staff.list_reservations'))

# --- Order Management ---

@staff_bp.route('/kitchen')
@role_required('restaurant_staff')
def kitchen_display():
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        flash("You must be assigned to a restaurant to access the kitchen display.", "warning")
        return redirect(url_for('staff.dashboard'))

    active_orders = Order.query.filter_by(restaurant_id=staff_record.restaurant_id).filter(
        Order.status.in_(['placed', 'confirmed', 'preparing', 'ready'])
    ).order_by(Order.created_at.asc()).all()

    placed_orders = [o for o in active_orders if o.status == 'placed']
    confirmed_orders = [o for o in active_orders if o.status == 'confirmed']
    preparing_orders = [o for o in active_orders if o.status == 'preparing']
    ready_orders = [o for o in active_orders if o.status == 'ready']
    now = datetime.now()

    return render_template('staff/kitchen.html',
                           restaurant=staff_record.restaurant,
                           staff_record=staff_record,
                           placed_orders=placed_orders,
                           confirmed_orders=confirmed_orders,
                           preparing_orders=preparing_orders,
                           ready_orders=ready_orders,
                           now=now)

@staff_bp.route('/orders')
@role_required('restaurant_staff')
def list_orders():
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        flash("You must be assigned to a restaurant to manage orders.", "warning")
        return redirect(url_for('staff.dashboard'))
        
    orders = Order.query.filter_by(restaurant_id=staff_record.restaurant_id).order_by(Order.created_at.desc()).all()
    return render_template('staff/orders.html', orders=orders, restaurant=staff_record.restaurant)

@staff_bp.route('/orders/<int:order_id>')
@role_required('restaurant_staff')
def order_detail(order_id):
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)
        
    order = Order.query.filter_by(id=order_id, restaurant_id=staff_record.restaurant_id).first_or_404()
    return render_template('staff/order_detail.html', order=order)

@staff_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@role_required('restaurant_staff')
def update_order_status(order_id):
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)
        
    order = Order.query.filter_by(id=order_id, restaurant_id=staff_record.restaurant_id).first_or_404()
    new_status = request.form.get('status')
    
    valid_transitions = {
        'placed': ['confirmed', 'preparing', 'cancelled'],
        'confirmed': ['preparing', 'cancelled'],
        'preparing': ['ready'],
        'ready': ['served'],
        'served': [],
        'cancelled': []
    }
    
    if new_status in valid_transitions.get(order.status, []):
        order.status = new_status
        db.session.commit()
        flash(f"Order status updated to {new_status}.", "success")
    else:
        flash(f"Invalid status transition from {order.status} to {new_status}.", "danger")
        
    next_url = request.form.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(request.referrer or url_for('staff.order_detail', order_id=order.id))

@staff_bp.route('/orders/<int:order_id>/receipt')
@role_required('restaurant_staff')
def view_receipt(order_id):
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)
    order = Order.query.filter_by(id=order_id, restaurant_id=staff_record.restaurant_id).first_or_404()
    return render_template('customer/receipt.html', order=order, is_internal=True)

