from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required
from app.utils import role_required
from app import db
from app.models.restaurant import Restaurant
from app.models.user import User

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@role_required('super_admin')
def dashboard():
    return {'message': 'Super Admin dashboard - protected'}

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
