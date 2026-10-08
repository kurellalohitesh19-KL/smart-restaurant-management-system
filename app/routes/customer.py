from flask import Blueprint, render_template, request, abort
from flask_login import login_required
from app.utils import role_required
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/dashboard')
@role_required('customer')
def dashboard():
    return render_template('customer/dashboard.html')

@customer_bp.route('/restaurants')
@role_required('customer')
def list_restaurants():
    query = Restaurant.query.filter_by(is_active=True)
    
    name_filter = request.args.get('name')
    city_filter = request.args.get('city')
    
    if name_filter:
        query = query.filter(Restaurant.name.ilike(f'%{name_filter}%'))
    if city_filter:
        query = query.filter(Restaurant.city.ilike(f'%{city_filter}%'))
        
    restaurants = query.all()
    return render_template('customer/restaurants.html', restaurants=restaurants)

@customer_bp.route('/restaurants/<int:restaurant_id>')
@role_required('customer')
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_active=True).first_or_404()
    # We can fetch available tables and menus directly here, or use separate routes.
    # The prompt explicitly suggested /customer/restaurants/<restaurant_id>/menu 
    # and /customer/restaurants/<restaurant_id>/tables, so I'll link to them.
    return render_template('customer/restaurant_detail.html', restaurant=restaurant)

@customer_bp.route('/restaurants/<int:restaurant_id>/menu')
@role_required('customer')
def restaurant_menu(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_active=True).first_or_404()
    categories = MenuCategory.query.filter_by(restaurant_id=restaurant.id, is_active=True).all()
    return render_template('customer/menu.html', restaurant=restaurant, categories=categories)

@customer_bp.route('/restaurants/<int:restaurant_id>/tables')
@role_required('customer')
def restaurant_tables(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_active=True).first_or_404()
    tables = Table.query.filter_by(restaurant_id=restaurant.id, status='available').all()
    return render_template('customer/tables.html', restaurant=restaurant, tables=tables)
