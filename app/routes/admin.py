from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required
from app.utils import role_required
from app import db
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.user import User
from app.models.table import Table
from app.models.reservation import Reservation
from app.models.order import Order
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@role_required('super_admin')
def dashboard():
    users = User.query.all()
    user_stats = {
        'customers': sum(1 for u in users if u.role == 'customer'),
        'owners': sum(1 for u in users if u.role == 'restaurant_owner'),
        'staff': sum(1 for u in users if u.role == 'restaurant_staff'),
        'admins': sum(1 for u in users if u.role == 'super_admin')
    }

    restaurants = Restaurant.query.all()
    res_stats = {
        'total': len(restaurants),
        'active': sum(1 for r in restaurants if r.is_active),
        'inactive': sum(1 for r in restaurants if not r.is_active)
    }

    tables = Table.query.all()
    table_stats = {
        'total': len(tables),
        'available': sum(1 for t in tables if t.status == 'available'),
        'reserved': sum(1 for t in tables if t.status == 'reserved'),
        'occupied': sum(1 for t in tables if t.status == 'occupied'),
        'maintenance': sum(1 for t in tables if t.status == 'maintenance')
    }

    reservations = Reservation.query.all()
    reservation_stats = {
        'total': len(reservations),
        'pending': sum(1 for r in reservations if r.status == 'pending'),
        'confirmed': sum(1 for r in reservations if r.status == 'confirmed'),
        'cancelled': sum(1 for r in reservations if r.status == 'cancelled'),
        'completed': sum(1 for r in reservations if r.status == 'completed')
    }

    orders = Order.query.all()
    order_stats = {
        'total': len(orders),
        'placed': sum(1 for o in orders if o.status == 'placed'),
        'confirmed': sum(1 for o in orders if o.status == 'confirmed'),
        'preparing': sum(1 for o in orders if o.status == 'preparing'),
        'ready': sum(1 for o in orders if o.status == 'ready'),
        'served': sum(1 for o in orders if o.status == 'served'),
        'cancelled': sum(1 for o in orders if o.status == 'cancelled')
    }

    return render_template('admin/dashboard.html',
                           user_stats=user_stats,
                           res_stats=res_stats,
                           table_stats=table_stats,
                           reservation_stats=reservation_stats,
                           order_stats=order_stats)

@admin_bp.route('/restaurants')
@role_required('super_admin')
def list_restaurants():
    restaurants = Restaurant.query.all()
    return render_template('admin/restaurants.html', restaurants=restaurants)

@admin_bp.route('/restaurants/create', methods=['GET', 'POST'])
@role_required('super_admin')
def create_restaurant():
    if request.method == 'POST':
        name = request.form.get('name')
        owner_id = request.form.get('owner_id')
        
        if not name or not owner_id:
            flash('Name and Owner are required.', 'danger')
            return redirect(url_for('admin.create_restaurant'))
            
        owner = User.query.get(owner_id)
        if not owner or owner.role != 'restaurant_owner':
            flash('Invalid owner selected. Owner must have restaurant_owner role.', 'danger')
            return redirect(url_for('admin.create_restaurant'))
            
        restaurant = Restaurant(
            name=name,
            owner_id=owner.id,
            description=request.form.get('description'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            latitude=request.form.get('latitude') or None,
            longitude=request.form.get('longitude') or None,
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(restaurant)
        db.session.commit()
        flash('Restaurant created successfully.', 'success')
        return redirect(url_for('admin.list_restaurants'))
        
    owners = User.query.filter_by(role='restaurant_owner').all()
    return render_template('admin/restaurant_form.html', owners=owners, restaurant=None)

@admin_bp.route('/restaurants/<int:restaurant_id>')
@role_required('super_admin')
def view_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    return render_template('admin/restaurant_form.html', restaurant=restaurant, view_only=True)

@admin_bp.route('/restaurants/<int:restaurant_id>/edit', methods=['GET', 'POST'])
@role_required('super_admin')
def edit_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        owner_id = request.form.get('owner_id')
        
        if not name or not owner_id:
            flash('Name and Owner are required.', 'danger')
            return redirect(url_for('admin.edit_restaurant', restaurant_id=restaurant.id))
            
        owner = User.query.get(owner_id)
        if not owner or owner.role != 'restaurant_owner':
            flash('Invalid owner selected. Owner must have restaurant_owner role.', 'danger')
            return redirect(url_for('admin.edit_restaurant', restaurant_id=restaurant.id))
            
        restaurant.name = name
        restaurant.owner_id = owner.id
        restaurant.description = request.form.get('description')
        restaurant.address = request.form.get('address')
        restaurant.city = request.form.get('city')
        restaurant.state = request.form.get('state')
        restaurant.latitude = request.form.get('latitude') or None
        restaurant.longitude = request.form.get('longitude') or None
        restaurant.phone = request.form.get('phone')
        restaurant.email = request.form.get('email')
        restaurant.is_active = request.form.get('is_active') == 'on'
        
        db.session.commit()
        flash('Restaurant updated successfully.', 'success')
        return redirect(url_for('admin.list_restaurants'))
        
    owners = User.query.filter_by(role='restaurant_owner').all()
    return render_template('admin/restaurant_form.html', owners=owners, restaurant=restaurant)
