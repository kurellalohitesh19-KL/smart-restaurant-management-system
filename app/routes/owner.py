from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils import role_required
from app import db
from app.models.restaurant import Restaurant

owner_bp = Blueprint('owner', __name__)

@owner_bp.route('/dashboard')
@role_required('restaurant_owner')
def dashboard():
    return {'message': 'Owner dashboard - protected'}

@owner_bp.route('/restaurant')
@role_required('restaurant_owner')
def view_restaurant():
    restaurant = Restaurant.query.filter_by(owner_id=current_user.id).first()
    if not restaurant:
        return render_template('owner/restaurant.html', restaurant=None, message="No restaurant has been assigned to your account.")
    return render_template('owner/restaurant.html', restaurant=restaurant)

@owner_bp.route('/restaurant/edit', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def edit_restaurant():
    restaurant = Restaurant.query.filter_by(owner_id=current_user.id).first()
    if not restaurant:
        flash("No restaurant has been assigned to your account.", "danger")
        return redirect(url_for('owner.view_restaurant'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash("Restaurant name is required.", "danger")
            return redirect(url_for('owner.edit_restaurant'))
            
        restaurant.name = name
        restaurant.description = request.form.get('description')
        restaurant.address = request.form.get('address')
        restaurant.city = request.form.get('city')
        restaurant.state = request.form.get('state')
        restaurant.latitude = request.form.get('latitude') or None
        restaurant.longitude = request.form.get('longitude') or None
        restaurant.phone = request.form.get('phone')
        restaurant.email = request.form.get('email')
        
        db.session.commit()
        flash('Restaurant updated successfully.', 'success')
        return redirect(url_for('owner.view_restaurant'))
        
    return render_template('owner/restaurant_form.html', restaurant=restaurant)

@owner_bp.route('/restaurants/<int:restaurant_id>')
@role_required('restaurant_owner')
def view_restaurant_by_id(restaurant_id):
    # Enforces explicit data isolation rule
    restaurant = Restaurant.query.filter_by(id=restaurant_id, owner_id=current_user.id).first_or_404()
    return render_template('owner/restaurant.html', restaurant=restaurant)

@owner_bp.route('/restaurants/<int:restaurant_id>/edit', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def edit_restaurant_by_id(restaurant_id):
    # Enforces explicit data isolation rule
    restaurant = Restaurant.query.filter_by(id=restaurant_id, owner_id=current_user.id).first_or_404()
    if request.method == 'POST':
        # Delegate to standard edit logic conceptually, or handle it here
        pass
    return render_template('owner/restaurant_form.html', restaurant=restaurant)
