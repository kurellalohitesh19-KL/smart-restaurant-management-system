from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response
from flask_login import login_required, current_user
from app.utils import role_required
from app import db
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem
from app.models.user import User
from app.models.reservation import Reservation
from app.models.order import Order, OrderItem
from app.models.restaurant import CustomerRestaurant
from app.services import reservation_service
from sqlalchemy import func
from datetime import datetime, timedelta, date, timezone
import csv
import io

owner_bp = Blueprint('owner', __name__)

@owner_bp.route('/dashboard')
@role_required('restaurant_owner')
def dashboard():
    restaurant = Restaurant.query.filter_by(owner_id=current_user.id).first()
    if not restaurant:
        return render_template('owner/dashboard.html', restaurant=None)

    # Tables
    tables = Table.query.filter_by(restaurant_id=restaurant.id).all()
    table_stats = {
        'total': len(tables),
        'available': sum(1 for t in tables if t.status == 'available'),
        'reserved': sum(1 for t in tables if t.status == 'reserved'),
        'occupied': sum(1 for t in tables if t.status == 'occupied'),
        'maintenance': sum(1 for t in tables if t.status == 'maintenance')
    }

    # Reservations
    today = datetime.now().date()
    reservations = Reservation.query.filter_by(restaurant_id=restaurant.id).all()
    res_stats = {
        'today': sum(1 for r in reservations if r.reservation_date == today),
        'pending': sum(1 for r in reservations if r.status == 'pending'),
        'confirmed': sum(1 for r in reservations if r.status == 'confirmed'),
        'completed': sum(1 for r in reservations if r.status == 'completed')
    }

    # Orders
    orders = Order.query.filter_by(restaurant_id=restaurant.id).all()
    def _is_today(dt):
        if not dt:
            return False
        if dt.tzinfo is not None:
            return dt.astimezone().date() == today
        return dt.date() == today or (dt.replace(tzinfo=timezone.utc).astimezone().date() == today)

    order_stats = {
        'today': sum(1 for o in orders if _is_today(o.created_at)),
        'pending': sum(1 for o in orders if o.status == 'placed'),
        'preparing': sum(1 for o in orders if o.status == 'preparing'),
        'ready': sum(1 for o in orders if o.status == 'ready'),
        'served': sum(1 for o in orders if o.status == 'served')
    }

    # Staff
    staff_count = RestaurantStaff.query.filter_by(restaurant_id=restaurant.id).count()

    # Customers
    customer_count = CustomerRestaurant.query.filter_by(restaurant_id=restaurant.id).count()

    recent_orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(Order.created_at.desc()).limit(5).all()
    recent_reservations = Reservation.query.filter_by(restaurant_id=restaurant.id).order_by(Reservation.reservation_date.desc(), Reservation.start_time.desc()).limit(5).all()

    return render_template(
        'owner/dashboard.html',
        restaurant=restaurant,
        tables=tables,
        table_stats=table_stats,
        res_stats=res_stats,
        order_stats=order_stats,
        staff_count=staff_count,
        customer_count=customer_count,
        recent_orders=recent_orders,
        recent_reservations=recent_reservations
    )

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
    restaurant = Restaurant.query.filter_by(id=restaurant_id, owner_id=current_user.id).first_or_404()
    return render_template('owner/restaurant.html', restaurant=restaurant)

@owner_bp.route('/restaurants/<int:restaurant_id>/edit', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def edit_restaurant_by_id(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, owner_id=current_user.id).first_or_404()
    if request.method == 'POST':
        pass
    return render_template('owner/restaurant_form.html', restaurant=restaurant)

# --- Staff Management ---

def get_owner_restaurant():
    return Restaurant.query.filter_by(owner_id=current_user.id).first()

@owner_bp.route('/staff')
@role_required('restaurant_owner')
def list_staff():
    restaurant = get_owner_restaurant()
    if not restaurant:
        flash("You must have an assigned restaurant to manage staff.", "warning")
        return redirect(url_for('owner.dashboard'))
        
    staff_members = RestaurantStaff.query.filter_by(restaurant_id=restaurant.id).all()
    return render_template('owner/staff.html', staff_members=staff_members, restaurant=restaurant)

@owner_bp.route('/staff/create', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def create_staff():
    restaurant = get_owner_restaurant()
    if not restaurant:
        flash("You must have an assigned restaurant to manage staff.", "warning")
        return redirect(url_for('owner.dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        designation = request.form.get('designation')
        
        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return redirect(url_for('owner.create_staff'))
            
        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
            return redirect(url_for('owner.create_staff'))
            
        new_user = User(
            name=name,
            email=email,
            phone=phone,
            role='restaurant_staff'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush() # get ID
        
        new_staff = RestaurantStaff(
            user_id=new_user.id,
            restaurant_id=restaurant.id,
            designation=designation,
            is_active=True
        )
        db.session.add(new_staff)
        db.session.commit()
        
        flash("Staff account created successfully.", "success")
        return redirect(url_for('owner.list_staff'))
        
    return render_template('owner/staff_form.html', staff=None)

@owner_bp.route('/staff/<int:staff_id>/edit', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def edit_staff(staff_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    staff = RestaurantStaff.query.filter_by(id=staff_id, restaurant_id=restaurant.id).first_or_404()
    user = User.query.get(staff.user_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        designation = request.form.get('designation')
        
        if not name or not email:
            flash("Name and email are required.", "danger")
            return redirect(url_for('owner.edit_staff', staff_id=staff.id))
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash("Email is already registered by another user.", "danger")
            return redirect(url_for('owner.edit_staff', staff_id=staff.id))
            
        user.name = name
        user.email = email
        user.phone = phone
        staff.designation = designation
        
        db.session.commit()
        flash("Staff account updated successfully.", "success")
        return redirect(url_for('owner.list_staff'))
        
    return render_template('owner/staff_form.html', staff=staff, user=user)

@owner_bp.route('/staff/<int:staff_id>/toggle', methods=['POST'])
@role_required('restaurant_owner')
def toggle_staff(staff_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    staff = RestaurantStaff.query.filter_by(id=staff_id, restaurant_id=restaurant.id).first_or_404()
    staff.is_active = not staff.is_active
    db.session.commit()
    
    status = "activated" if staff.is_active else "deactivated"
    flash(f"Staff account {status} successfully.", "success")
    return redirect(url_for('owner.list_staff'))

# --- Table Management ---

@owner_bp.route('/tables')
@role_required('restaurant_owner')
def list_tables():
    restaurant = get_owner_restaurant()
    if not restaurant:
        flash("You must have an assigned restaurant to manage tables.", "warning")
        return redirect(url_for('owner.dashboard'))
        
    tables = Table.query.filter_by(restaurant_id=restaurant.id).all()
    return render_template('owner/tables.html', tables=tables, restaurant=restaurant)

@owner_bp.route('/tables/create', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def create_table():
    restaurant = get_owner_restaurant()
    if not restaurant:
        flash("You must have an assigned restaurant to manage tables.", "warning")
        return redirect(url_for('owner.dashboard'))
        
    if request.method == 'POST':
        table_number = request.form.get('table_number')
        capacity = request.form.get('capacity')
        status = request.form.get('status')
        
        if not table_number or not capacity:
            flash("Table number and capacity are required.", "danger")
            return redirect(url_for('owner.create_table'))
            
        try:
            capacity = int(capacity)
            if capacity <= 0:
                raise ValueError
        except ValueError:
            flash("Capacity must be a positive integer.", "danger")
            return redirect(url_for('owner.create_table'))
            
        valid_statuses = ['available', 'reserved', 'occupied', 'maintenance']
        if status not in valid_statuses:
            flash("Invalid status selected.", "danger")
            return redirect(url_for('owner.create_table'))
            
        existing = Table.query.filter_by(restaurant_id=restaurant.id, table_number=table_number).first()
        if existing:
            flash("Table number already exists in your restaurant.", "danger")
            return redirect(url_for('owner.create_table'))
            
        new_table = Table(
            restaurant_id=restaurant.id,
            table_number=table_number,
            capacity=capacity,
            status=status
        )
        db.session.add(new_table)
        db.session.commit()
        
        flash("Table created successfully.", "success")
        return redirect(url_for('owner.list_tables'))
        
    return render_template('owner/table_form.html', table=None)

@owner_bp.route('/tables/<int:table_id>/edit', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def edit_table(table_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    table = Table.query.filter_by(id=table_id, restaurant_id=restaurant.id).first_or_404()
    
    if request.method == 'POST':
        table_number = request.form.get('table_number')
        capacity = request.form.get('capacity')
        status = request.form.get('status')
        
        if not table_number or not capacity:
            flash("Table number and capacity are required.", "danger")
            return redirect(url_for('owner.edit_table', table_id=table.id))
            
        try:
            capacity = int(capacity)
            if capacity <= 0:
                raise ValueError
        except ValueError:
            flash("Capacity must be a positive integer.", "danger")
            return redirect(url_for('owner.edit_table', table_id=table.id))
            
        valid_statuses = ['available', 'reserved', 'occupied', 'maintenance']
        if status not in valid_statuses:
            flash("Invalid status selected.", "danger")
            return redirect(url_for('owner.edit_table', table_id=table.id))
            
        if table_number != table.table_number:
            existing = Table.query.filter_by(restaurant_id=restaurant.id, table_number=table_number).first()
            if existing:
                flash("Table number already exists in your restaurant.", "danger")
                return redirect(url_for('owner.edit_table', table_id=table.id))
                
        table.table_number = table_number
        table.capacity = capacity
        table.status = status
        db.session.commit()
        
        flash("Table updated successfully.", "success")
        return redirect(url_for('owner.list_tables'))
        
    return render_template('owner/table_form.html', table=table)

@owner_bp.route('/tables/<int:table_id>/delete', methods=['POST'])
@role_required('restaurant_owner')
def delete_table(table_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    table = Table.query.filter_by(id=table_id, restaurant_id=restaurant.id).first_or_404()
    
    # Check dependencies (active reservations/orders)
    # Using basic checks on the relationships since we don't have reservation logic fully implemented yet.
    # If the table has ANY reservations or orders associated, block deletion for safety (as requested).
    if getattr(table, 'reservations', None) or getattr(table, 'orders', None):
        flash("Cannot delete table: active reservations or orders exist.", "danger")
        return redirect(url_for('owner.list_tables'))
        
    db.session.delete(table)
    db.session.commit()
    flash("Table deleted successfully.", "success")
    return redirect(url_for('owner.list_tables'))

# --- Menu Management ---

@owner_bp.route('/menu')
@role_required('restaurant_owner')
def view_menu():
    restaurant = get_owner_restaurant()
    if not restaurant:
        flash("You must have an assigned restaurant to manage the menu.", "warning")
        return redirect(url_for('owner.dashboard'))
        
    categories = MenuCategory.query.filter_by(restaurant_id=restaurant.id).all()
    # The template can access category.items if the relationship is set, 
    # but let's fetch items directly if needed, or rely on relationship.
    # MenuCategory has `items = db.relationship('MenuItem', backref='category', lazy=True)`
    return render_template('owner/menu.html', categories=categories, restaurant=restaurant)

@owner_bp.route('/menu/categories/create', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def create_category():
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'on'
        
        if not name:
            flash("Category name is required.", "danger")
            return redirect(url_for('owner.create_category'))
            
        category = MenuCategory(
            restaurant_id=restaurant.id,
            name=name,
            description=description,
            is_active=is_active
        )
        db.session.add(category)
        db.session.commit()
        flash("Category created successfully.", "success")
        return redirect(url_for('owner.view_menu'))
        
    return render_template('owner/category_form.html', category=None)

@owner_bp.route('/menu/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def edit_category(category_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    category = MenuCategory.query.filter_by(id=category_id, restaurant_id=restaurant.id).first_or_404()
    
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash("Category name is required.", "danger")
            return redirect(url_for('owner.edit_category', category_id=category.id))
            
        category.name = name
        category.description = request.form.get('description')
        category.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash("Category updated successfully.", "success")
        return redirect(url_for('owner.view_menu'))
        
    return render_template('owner/category_form.html', category=category)

@owner_bp.route('/menu/categories/<int:category_id>/delete', methods=['POST'])
@role_required('restaurant_owner')
def delete_category(category_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    category = MenuCategory.query.filter_by(id=category_id, restaurant_id=restaurant.id).first_or_404()
    
    if category.items:
        flash("Cannot delete category with existing menu items.", "danger")
        return redirect(url_for('owner.view_menu'))
        
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted successfully.", "success")
    return redirect(url_for('owner.view_menu'))

@owner_bp.route('/menu/items/create', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def create_menu_item():
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    categories = MenuCategory.query.filter_by(restaurant_id=restaurant.id).all()
    if not categories:
        flash("Please create a category first.", "warning")
        return redirect(url_for('owner.create_category'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        price = request.form.get('price')
        
        if not name or not category_id or not price:
            flash("Name, category, and price are required.", "danger")
            return redirect(url_for('owner.create_menu_item'))
            
        category = MenuCategory.query.filter_by(id=category_id, restaurant_id=restaurant.id).first()
        if not category:
            flash("Invalid category selected.", "danger")
            return redirect(url_for('owner.create_menu_item'))
            
        try:
            price = float(price)
            if price < 0:
                raise ValueError
        except ValueError:
            flash("Price must be a valid number greater than or equal to zero.", "danger")
            return redirect(url_for('owner.create_menu_item'))
            
        item = MenuItem(
            restaurant_id=restaurant.id,
            category_id=category.id,
            name=name,
            description=request.form.get('description'),
            price=price,
            is_available=request.form.get('is_available') == 'on'
        )
        db.session.add(item)
        db.session.commit()
        flash("Menu item created successfully.", "success")
        return redirect(url_for('owner.view_menu'))
        
    return render_template('owner/menu_item_form.html', item=None, categories=categories)

@owner_bp.route('/menu/items/<int:item_id>/edit', methods=['GET', 'POST'])
@role_required('restaurant_owner')
def edit_menu_item(item_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=restaurant.id).first_or_404()
    categories = MenuCategory.query.filter_by(restaurant_id=restaurant.id).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        price = request.form.get('price')
        
        if not name or not category_id or not price:
            flash("Name, category, and price are required.", "danger")
            return redirect(url_for('owner.edit_menu_item', item_id=item.id))
            
        category = MenuCategory.query.filter_by(id=category_id, restaurant_id=restaurant.id).first()
        if not category:
            flash("Invalid category selected.", "danger")
            return redirect(url_for('owner.edit_menu_item', item_id=item.id))
            
        try:
            price = float(price)
            if price < 0:
                raise ValueError
        except ValueError:
            flash("Price must be a valid number greater than or equal to zero.", "danger")
            return redirect(url_for('owner.edit_menu_item', item_id=item.id))
            
        item.name = name
        item.category_id = category.id
        item.price = price
        item.description = request.form.get('description')
        item.is_available = request.form.get('is_available') == 'on'
        
        db.session.commit()
        flash("Menu item updated successfully.", "success")
        return redirect(url_for('owner.view_menu'))
        
    return render_template('owner/menu_item_form.html', item=item, categories=categories)

@owner_bp.route('/menu/items/<int:item_id>/delete', methods=['POST'])
@role_required('restaurant_owner')
def delete_menu_item(item_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=restaurant.id).first_or_404()
    
    if getattr(item, 'order_items', None):
        flash("Cannot delete menu item with associated orders.", "danger")
        return redirect(url_for('owner.view_menu'))
        
    db.session.delete(item)
    db.session.commit()
    flash("Menu item deleted successfully.", "success")
    return redirect(url_for('owner.view_menu'))

# --- Reservation Management ---

@owner_bp.route('/reservations')
@role_required('restaurant_owner')
def list_reservations():
    restaurant = get_owner_restaurant()
    if not restaurant:
        flash("You must have an assigned restaurant to manage reservations.", "warning")
        return redirect(url_for('owner.dashboard'))
        
    reservations = Reservation.query.filter_by(restaurant_id=restaurant.id).order_by(Reservation.reservation_date.desc(), Reservation.start_time.desc()).all()
    return render_template('owner/reservations.html', reservations=reservations, restaurant=restaurant)

@owner_bp.route('/reservations/<int:reservation_id>/confirm', methods=['POST'])
@role_required('restaurant_owner')
def confirm_reservation(reservation_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)

    reservation = Reservation.query.filter_by(id=reservation_id, restaurant_id=restaurant.id).first_or_404()
    if reservation.status == 'pending':
        reservation_service.confirm_reservation(reservation)
        flash('Reservation confirmed successfully.', 'success')
    else:
        flash('Only pending reservations can be confirmed.', 'error')
    return redirect(url_for('owner.list_reservations'))

@owner_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@role_required('restaurant_owner')
def cancel_reservation(reservation_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)

    reservation = Reservation.query.filter_by(id=reservation_id, restaurant_id=restaurant.id).first_or_404()
    if reservation.status in ['pending', 'confirmed']:
        reservation_service.cancel_reservation(reservation)
        flash('Reservation cancelled successfully.', 'success')
    else:
        flash('Reservation cannot be cancelled.', 'error')
    return redirect(url_for('owner.list_reservations'))

@owner_bp.route('/reservations/<int:reservation_id>/complete', methods=['POST'])
@role_required('restaurant_owner')
def complete_reservation(reservation_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)

    reservation = Reservation.query.filter_by(id=reservation_id, restaurant_id=restaurant.id).first_or_404()
    if reservation.status == 'confirmed':
        try:
            reservation_service.checkout_reservation(reservation)
            flash('Reservation marked as completed and table released.', 'success')
        except ValueError as e:
            flash(str(e), 'danger')
    else:
        flash('Only confirmed reservations can be marked as completed.', 'error')
    return redirect(url_for('owner.list_reservations'))


@owner_bp.route('/reservations/<int:reservation_id>/checkin', methods=['POST'])
@role_required('restaurant_owner')
def checkin_reservation(reservation_id):
    """Mark customer as physically seated — table becomes 'occupied'."""
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)

    reservation = Reservation.query.filter_by(id=reservation_id, restaurant_id=restaurant.id).first_or_404()
    if reservation.status == 'confirmed':
        try:
            reservation_service.checkin_reservation(reservation)
            flash('Customer checked in — table marked as occupied.', 'success')
        except ValueError as e:
            flash(str(e), 'danger')
    else:
        flash('Only confirmed reservations can be checked in.', 'error')
    return redirect(url_for('owner.list_reservations'))

# --- Order Management ---

@owner_bp.route('/kitchen')
@role_required('restaurant_owner')
def kitchen_display():
    restaurant = get_owner_restaurant()
    if not restaurant:
        flash("You must have an assigned restaurant to access the kitchen display.", "warning")
        return redirect(url_for('owner.dashboard'))

    active_orders = Order.query.filter_by(restaurant_id=restaurant.id).filter(
        Order.status.in_(['placed', 'confirmed', 'preparing', 'ready'])
    ).order_by(Order.created_at.asc()).all()

    placed_orders = [o for o in active_orders if o.status == 'placed']
    confirmed_orders = [o for o in active_orders if o.status == 'confirmed']
    preparing_orders = [o for o in active_orders if o.status == 'preparing']
    ready_orders = [o for o in active_orders if o.status == 'ready']
    now = datetime.now()

    return render_template('owner/kitchen.html',
                           restaurant=restaurant,
                           placed_orders=placed_orders,
                           confirmed_orders=confirmed_orders,
                           preparing_orders=preparing_orders,
                           ready_orders=ready_orders,
                           now=now)

@owner_bp.route('/orders')
@role_required('restaurant_owner')
def list_orders():
    restaurant = get_owner_restaurant()
    if not restaurant:
        flash("You must have an assigned restaurant to manage orders.", "warning")
        return redirect(url_for('owner.dashboard'))
        
    orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(Order.created_at.desc()).all()
    return render_template('owner/orders.html', orders=orders, restaurant=restaurant)

@owner_bp.route('/orders/<int:order_id>')
@role_required('restaurant_owner')
def order_detail(order_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    order = Order.query.filter_by(id=order_id, restaurant_id=restaurant.id).first_or_404()
    return render_template('owner/order_detail.html', order=order)

@owner_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@role_required('restaurant_owner')
def update_order_status(order_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
        
    order = Order.query.filter_by(id=order_id, restaurant_id=restaurant.id).first_or_404()
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
    return redirect(request.referrer or url_for('owner.order_detail', order_id=order.id))

@owner_bp.route('/orders/<int:order_id>/receipt')
@role_required('restaurant_owner')
def view_receipt(order_id):
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)
    order = Order.query.filter_by(id=order_id, restaurant_id=restaurant.id).first_or_404()
    return render_template('customer/receipt.html', order=order, is_internal=True)

# --- Analytics and Reporting ---

def _parse_date_range(req):
    start_str = req.args.get('start_date')
    end_str = req.args.get('end_date')
    today = date.today()
    default_start = today - timedelta(days=30)
    
    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else default_start
    except (ValueError, TypeError):
        start_date = default_start
        
    try:
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else today
    except (ValueError, TypeError):
        end_date = today

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    return start_date, end_date

@owner_bp.route('/reports')
@role_required('restaurant_owner')
def reports():
    restaurant = get_owner_restaurant()
    if not restaurant:
        flash("You must have an assigned restaurant to view reports.", "warning")
        return redirect(url_for('owner.dashboard'))

    start_date, end_date = _parse_date_range(request)
    next_day = end_date + timedelta(days=1)

    orders = Order.query.filter(
        Order.restaurant_id == restaurant.id,
        Order.created_at >= start_date,
        Order.created_at < next_day
    ).order_by(Order.created_at.desc()).all()

    reservations = Reservation.query.filter(
        Reservation.restaurant_id == restaurant.id,
        Reservation.reservation_date >= start_date,
        Reservation.reservation_date <= end_date
    ).order_by(Reservation.reservation_date.desc(), Reservation.start_time.desc()).all()

    total_sales = sum(o.total_amount for o in orders if o.status != 'cancelled')
    orders_count = len(orders)
    served_orders_count = sum(1 for o in orders if o.status == 'served')
    cancelled_orders_count = sum(1 for o in orders if o.status == 'cancelled')
    avg_order_value = (float(total_sales) / orders_count) if orders_count > 0 else 0.0

    res_count = len(reservations)
    confirmed_res_count = sum(1 for r in reservations if r.status == 'confirmed')
    completed_res_count = sum(1 for r in reservations if r.status == 'completed')
    cancelled_res_count = sum(1 for r in reservations if r.status == 'cancelled')

    top_items_query = db.session.query(
        MenuItem.name,
        func.sum(OrderItem.quantity).label('qty_sold'),
        func.sum(OrderItem.subtotal).label('revenue')
    ).join(OrderItem, MenuItem.id == OrderItem.menu_item_id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(
         Order.restaurant_id == restaurant.id,
         Order.created_at >= start_date,
         Order.created_at < next_day,
         Order.status != 'cancelled'
     ).group_by(MenuItem.name)\
      .order_by(func.sum(OrderItem.quantity).desc())\
      .limit(5).all()

    all_tables = Table.query.filter_by(restaurant_id=restaurant.id).all()
    occupied_count = sum(1 for t in all_tables if t.status == 'occupied')
    reserved_count = sum(1 for t in all_tables if t.status == 'reserved')
    available_count = sum(1 for t in all_tables if t.status == 'available')
    utilization_rate = (occupied_count / len(all_tables) * 100) if all_tables else 0

    return render_template('owner/reports.html',
                           restaurant=restaurant,
                           start_date=start_date.strftime('%Y-%m-%d'),
                           end_date=end_date.strftime('%Y-%m-%d'),
                           total_sales=total_sales,
                           orders_count=orders_count,
                           served_orders_count=served_orders_count,
                           cancelled_orders_count=cancelled_orders_count,
                           avg_order_value=avg_order_value,
                           res_count=res_count,
                           confirmed_res_count=confirmed_res_count,
                           completed_res_count=completed_res_count,
                           cancelled_res_count=cancelled_res_count,
                           top_items=top_items_query,
                           all_tables=all_tables,
                           occupied_count=occupied_count,
                           reserved_count=reserved_count,
                           available_count=available_count,
                           utilization_rate=utilization_rate,
                           orders=orders[:20])

def _safe_csv_val(val):
    if val is None:
        return ""
    s = str(val)
    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + s
    return s

@owner_bp.route('/reports/export/orders')
@role_required('restaurant_owner')
def export_orders_csv():
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)

    start_date, end_date = _parse_date_range(request)
    next_day = end_date + timedelta(days=1)

    orders = Order.query.filter(
        Order.restaurant_id == restaurant.id,
        Order.created_at >= start_date,
        Order.created_at < next_day
    ).order_by(Order.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order ID', 'Date & Time', 'Customer Name', 'Customer Email', 'Table Number', 'Status', 'Items Count', 'Total Amount (INR)'])

    for o in orders:
        writer.writerow([
            _safe_csv_val(o.id),
            _safe_csv_val(o.created_at.strftime('%Y-%m-%d %H:%M:%S') if o.created_at else ''),
            _safe_csv_val(o.customer.name if o.customer else ''),
            _safe_csv_val(o.customer.email if o.customer else ''),
            _safe_csv_val(o.table.table_number if o.table else 'N/A'),
            _safe_csv_val(o.status.title()),
            _safe_csv_val(len(o.items)),
            _safe_csv_val(f"{float(o.total_amount):.2f}")
        ])

    filename = f"orders_{restaurant.id}_{start_date}_{end_date}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@owner_bp.route('/reports/export/reservations')
@role_required('restaurant_owner')
def export_reservations_csv():
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)

    start_date, end_date = _parse_date_range(request)

    reservations = Reservation.query.filter(
        Reservation.restaurant_id == restaurant.id,
        Reservation.reservation_date >= start_date,
        Reservation.reservation_date <= end_date
    ).order_by(Reservation.reservation_date.desc(), Reservation.start_time.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Reservation ID', 'Date', 'Start Time', 'End Time', 'Customer Name', 'Customer Email', 'Customer Phone', 'Table Number', 'Guests', 'Status'])

    for r in reservations:
        writer.writerow([
            _safe_csv_val(r.id),
            _safe_csv_val(r.reservation_date.strftime('%Y-%m-%d')),
            _safe_csv_val(r.start_time.strftime('%H:%M')),
            _safe_csv_val(r.end_time.strftime('%H:%M')),
            _safe_csv_val(r.customer.name if r.customer else ''),
            _safe_csv_val(r.customer.email if r.customer else ''),
            _safe_csv_val(r.customer.phone if r.customer else ''),
            _safe_csv_val(r.table.table_number if r.table else 'N/A'),
            _safe_csv_val(r.number_of_guests),
            _safe_csv_val(r.status.title())
        ])

    filename = f"reservations_{restaurant.id}_{start_date}_{end_date}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@owner_bp.route('/reports/export/sales')
@role_required('restaurant_owner')
def export_sales_csv():
    restaurant = get_owner_restaurant()
    if not restaurant:
        abort(403)

    start_date, end_date = _parse_date_range(request)
    next_day = end_date + timedelta(days=1)

    top_items_query = db.session.query(
        MenuItem.name,
        MenuCategory.name.label('category_name'),
        MenuItem.price,
        func.sum(OrderItem.quantity).label('qty_sold'),
        func.sum(OrderItem.subtotal).label('revenue')
    ).join(OrderItem, MenuItem.id == OrderItem.menu_item_id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .join(MenuCategory, MenuItem.category_id == MenuCategory.id)\
     .filter(
         Order.restaurant_id == restaurant.id,
         Order.created_at >= start_date,
         Order.created_at < next_day,
         Order.status != 'cancelled'
     ).group_by(MenuItem.name, MenuCategory.name, MenuItem.price)\
      .order_by(func.sum(OrderItem.subtotal).desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Item Name', 'Category', 'Unit Price (INR)', 'Quantity Sold', 'Total Revenue (INR)'])

    for row in top_items_query:
        writer.writerow([
            _safe_csv_val(row.name),
            _safe_csv_val(row.category_name),
            _safe_csv_val(f"{float(row.price):.2f}"),
            _safe_csv_val(row.qty_sold),
            _safe_csv_val(f"{float(row.revenue):.2f}")
        ])

    filename = f"sales_items_{restaurant.id}_{start_date}_{end_date}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

