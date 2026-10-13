from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required
from app.utils import role_required
from app import db
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.user import User
from app.models.table import Table
from app.models.reservation import Reservation
from app.models.order import Order
from app.models.menu import MenuCategory, MenuItem
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

# --- Staff Management ---

@admin_bp.route('/staff')
@role_required('super_admin')
def list_staff():
    restaurant_id = request.args.get('restaurant_id', type=int)
    
    query = RestaurantStaff.query
    if restaurant_id:
        query = query.filter_by(restaurant_id=restaurant_id)
        
    staff_members = query.all()
    restaurants = Restaurant.query.all()
    
    return render_template('admin/staff.html', staff_members=staff_members, restaurants=restaurants, current_filter=restaurant_id)

@admin_bp.route('/staff/create', methods=['GET', 'POST'])
@role_required('super_admin')
def create_staff():
    restaurants = Restaurant.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        designation = request.form.get('designation')
        restaurant_id = request.form.get('restaurant_id', type=int)

        if not name or not email or not password or not restaurant_id:
            flash("Name, email, password, and assigned restaurant are required.", "danger")
            return redirect(url_for('admin.create_staff'))

        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
            return redirect(url_for('admin.create_staff'))

        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            flash("Invalid restaurant selected.", "danger")
            return redirect(url_for('admin.create_staff'))

        new_user = User(
            name=name,
            email=email,
            phone=phone,
            role='restaurant_staff'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        new_staff = RestaurantStaff(
            user_id=new_user.id,
            restaurant_id=restaurant.id,
            designation=designation,
            is_active=True
        )
        db.session.add(new_staff)
        db.session.commit()

        flash("Staff account created successfully.", "success")
        return redirect(url_for('admin.list_staff'))

    return render_template('admin/staff_form.html', staff=None, user=None, restaurants=restaurants, view_only=False)

@admin_bp.route('/staff/<int:staff_id>')
@role_required('super_admin')
def view_staff(staff_id):
    staff = RestaurantStaff.query.get_or_404(staff_id)
    user = User.query.get(staff.user_id)
    return render_template('admin/staff_form.html', staff=staff, user=user, view_only=True)

@admin_bp.route('/staff/<int:staff_id>/edit', methods=['GET', 'POST'])
@role_required('super_admin')
def edit_staff(staff_id):
    staff = RestaurantStaff.query.get_or_404(staff_id)
    user = User.query.get(staff.user_id)
    restaurants = Restaurant.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        designation = request.form.get('designation')
        restaurant_id = request.form.get('restaurant_id')
        
        if not name or not email or not restaurant_id:
            flash("Name, email, and restaurant are required.", "danger")
            return redirect(url_for('admin.edit_staff', staff_id=staff.id))
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash("Email is already registered by another user.", "danger")
            return redirect(url_for('admin.edit_staff', staff_id=staff.id))
            
        user.name = name
        user.email = email
        user.phone = phone
        staff.designation = designation
        staff.restaurant_id = restaurant_id
        
        db.session.commit()
        flash("Staff account updated successfully.", "success")
        return redirect(url_for('admin.list_staff'))
        
    return render_template('admin/staff_form.html', staff=staff, user=user, restaurants=restaurants)

@admin_bp.route('/staff/<int:staff_id>/toggle', methods=['POST'])
@role_required('super_admin')
def toggle_staff(staff_id):
    staff = RestaurantStaff.query.get_or_404(staff_id)
    staff.is_active = not staff.is_active
    db.session.commit()
    
    status = "activated" if staff.is_active else "deactivated"
    flash(f"Staff account {status} successfully.", "success")
    return redirect(url_for('admin.list_staff'))

# --- Customer Management ---

@admin_bp.route('/customers')
@role_required('super_admin')
def list_customers():
    search = request.args.get('search', '')
    query = User.query.filter_by(role='customer')
    
    if search:
        query = query.filter((User.name.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%')))
        
    customers = query.all()
    return render_template('admin/customers.html', customers=customers, search=search)

@admin_bp.route('/customers/<int:customer_id>')
@role_required('super_admin')
def view_customer(customer_id):
    customer = User.query.filter_by(id=customer_id, role='customer').first_or_404()
    return render_template('admin/customer_view.html', customer=customer)

@admin_bp.route('/customers/<int:customer_id>/toggle', methods=['POST'])
@role_required('super_admin')
def toggle_customer(customer_id):
    customer = User.query.filter_by(id=customer_id, role='customer').first_or_404()
    customer.is_active = not customer.is_active
    db.session.commit()
    
    status = "activated" if customer.is_active else "deactivated"
    flash(f"Customer account {status} successfully.", "success")
    return redirect(url_for('admin.list_customers'))

# --- Table Management ---

@admin_bp.route('/tables')
@role_required('super_admin')
def list_tables():
    restaurant_id = request.args.get('restaurant_id', type=int)
    search = request.args.get('search', '')
    
    query = Table.query
    if restaurant_id:
        query = query.filter_by(restaurant_id=restaurant_id)
    if search:
        query = query.filter(Table.table_number.ilike(f'%{search}%'))
        
    tables = query.all()
    restaurants = Restaurant.query.all()
    
    return render_template('admin/tables.html', tables=tables, restaurants=restaurants, current_filter=restaurant_id, search=search)

@admin_bp.route('/tables/<int:table_id>/edit', methods=['GET', 'POST'])
@role_required('super_admin')
def edit_table(table_id):
    table = Table.query.get_or_404(table_id)
    restaurants = Restaurant.query.all()
    
    if request.method == 'POST':
        table_number = request.form.get('table_number')
        capacity = request.form.get('capacity')
        status = request.form.get('status')
        restaurant_id = request.form.get('restaurant_id')
        
        if not table_number or not capacity or not restaurant_id:
            flash("Table number, capacity, and restaurant are required.", "danger")
            return redirect(url_for('admin.edit_table', table_id=table.id))
            
        try:
            capacity = int(capacity)
            if capacity <= 0:
                raise ValueError
            restaurant_id = int(restaurant_id)
        except ValueError:
            flash("Capacity and restaurant must be valid.", "danger")
            return redirect(url_for('admin.edit_table', table_id=table.id))
            
        valid_statuses = ['available', 'reserved', 'occupied', 'maintenance']
        if status not in valid_statuses:
            flash("Invalid status selected.", "danger")
            return redirect(url_for('admin.edit_table', table_id=table.id))
            
        if table_number != table.table_number or restaurant_id != table.restaurant_id:
            existing = Table.query.filter_by(restaurant_id=restaurant_id, table_number=table_number).first()
            if existing:
                flash("Table number already exists in the selected restaurant.", "danger")
                return redirect(url_for('admin.edit_table', table_id=table.id))
                
        table.table_number = table_number
        table.capacity = capacity
        table.status = status
        table.restaurant_id = restaurant_id
        db.session.commit()
        
        flash("Table updated successfully.", "success")
        return redirect(url_for('admin.list_tables'))
        
    return render_template('admin/table_form.html', table=table, restaurants=restaurants)

# --- Menu Management ---

@admin_bp.route('/menus')
@role_required('super_admin')
def list_menus():
    restaurant_id = request.args.get('restaurant_id', type=int)
    search = request.args.get('search', '')
    
    query = MenuItem.query
    cat_query = MenuCategory.query
    
    if restaurant_id:
        query = query.filter_by(restaurant_id=restaurant_id)
        cat_query = cat_query.filter_by(restaurant_id=restaurant_id)
        
    if search:
        query = query.filter(MenuItem.name.ilike(f'%{search}%'))
        
    items = query.all()
    categories = cat_query.all()
    restaurants = Restaurant.query.all()
    
    return render_template('admin/menus.html', items=items, categories=categories, restaurants=restaurants, current_filter=restaurant_id, search=search)

@admin_bp.route('/menus/categories/create', methods=['GET', 'POST'])
@role_required('super_admin')
def create_category():
    restaurants = Restaurant.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        restaurant_id = request.form.get('restaurant_id')
        is_active = request.form.get('is_active') == 'on'
        
        if not name or not restaurant_id:
            flash("Category name and restaurant are required.", "danger")
            return redirect(url_for('admin.create_category'))
            
        category = MenuCategory(
            restaurant_id=restaurant_id,
            name=name,
            description=description,
            is_active=is_active
        )
        db.session.add(category)
        db.session.commit()
        flash("Category created successfully.", "success")
        return redirect(url_for('admin.list_menus'))
        
    return render_template('admin/menu_category_form.html', category=None, restaurants=restaurants)

@admin_bp.route('/menus/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@role_required('super_admin')
def edit_category(category_id):
    category = MenuCategory.query.get_or_404(category_id)
    restaurants = Restaurant.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        restaurant_id = request.form.get('restaurant_id')
        
        if not name or not restaurant_id:
            flash("Category name and restaurant are required.", "danger")
            return redirect(url_for('admin.edit_category', category_id=category.id))
            
        category.name = name
        category.description = request.form.get('description')
        category.restaurant_id = restaurant_id
        category.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash("Category updated successfully.", "success")
        return redirect(url_for('admin.list_menus'))
        
    return render_template('admin/menu_category_form.html', category=category, restaurants=restaurants)

@admin_bp.route('/menus/items/create', methods=['GET', 'POST'])
@role_required('super_admin')
def create_menu_item():
    restaurants = Restaurant.query.all()
    categories = MenuCategory.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        price = request.form.get('price')
        restaurant_id = request.form.get('restaurant_id')
        
        if not name or not category_id or not price or not restaurant_id:
            flash("Name, category, price, and restaurant are required.", "danger")
            return redirect(url_for('admin.create_menu_item'))
            
        try:
            price = float(price)
            if price < 0:
                raise ValueError
        except ValueError:
            flash("Price must be a valid positive number.", "danger")
            return redirect(url_for('admin.create_menu_item'))
            
        item = MenuItem(
            restaurant_id=restaurant_id,
            category_id=category_id,
            name=name,
            description=request.form.get('description'),
            price=price,
            is_available=request.form.get('is_available') == 'on'
        )
        db.session.add(item)
        db.session.commit()
        flash("Menu item created successfully.", "success")
        return redirect(url_for('admin.list_menus'))
        
    return render_template('admin/menu_item_form.html', item=None, restaurants=restaurants, categories=categories)

@admin_bp.route('/menus/items/<int:item_id>/edit', methods=['GET', 'POST'])
@role_required('super_admin')
def edit_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    restaurants = Restaurant.query.all()
    categories = MenuCategory.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        price = request.form.get('price')
        restaurant_id = request.form.get('restaurant_id')
        
        if not name or not category_id or not price or not restaurant_id:
            flash("Name, category, price, and restaurant are required.", "danger")
            return redirect(url_for('admin.edit_menu_item', item_id=item.id))
            
        try:
            price = float(price)
            if price < 0:
                raise ValueError
        except ValueError:
            flash("Price must be a valid positive number.", "danger")
            return redirect(url_for('admin.edit_menu_item', item_id=item.id))
            
        item.name = name
        item.category_id = category_id
        item.price = price
        item.restaurant_id = restaurant_id
        item.description = request.form.get('description')
        item.is_available = request.form.get('is_available') == 'on'
        
        db.session.commit()
        flash("Menu item updated successfully.", "success")
        return redirect(url_for('admin.list_menus'))
        
    return render_template('admin/menu_item_form.html', item=item, restaurants=restaurants, categories=categories)

# --- Reservation Management ---

@admin_bp.route('/reservations')
@role_required('super_admin')
def list_reservations():
    restaurant_id = request.args.get('restaurant_id', type=int)
    status = request.args.get('status', '')
    date = request.args.get('date', '')
    
    query = Reservation.query
    
    if restaurant_id:
        query = query.filter_by(restaurant_id=restaurant_id)
    if status:
        query = query.filter_by(status=status)
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter_by(reservation_date=filter_date)
        except ValueError:
            pass
            
    reservations = query.order_by(Reservation.reservation_date.desc(), Reservation.start_time.desc()).all()
    restaurants = Restaurant.query.all()
    
    return render_template('admin/reservations.html', 
                           reservations=reservations, 
                           restaurants=restaurants, 
                           current_restaurant=restaurant_id, 
                           current_status=status, 
                           current_date=date)

@admin_bp.route('/reservations/<int:reservation_id>')
@role_required('super_admin')
def view_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    return render_template('admin/reservation_view.html', reservation=reservation)

@admin_bp.route('/reservations/<int:reservation_id>/confirm', methods=['POST'])
@role_required('super_admin')
def confirm_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.status == 'pending':
        reservation.status = 'confirmed'
        db.session.commit()
        flash('Reservation confirmed successfully.', 'success')
    else:
        flash('Only pending reservations can be confirmed.', 'error')
    return redirect(url_for('admin.view_reservation', reservation_id=reservation.id))

@admin_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@role_required('super_admin')
def cancel_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.status in ['pending', 'confirmed']:
        reservation.status = 'cancelled'
        db.session.commit()
        flash('Reservation cancelled successfully.', 'success')
    else:
        flash('Reservation cannot be cancelled.', 'error')
    return redirect(url_for('admin.view_reservation', reservation_id=reservation.id))

@admin_bp.route('/reservations/<int:reservation_id>/complete', methods=['POST'])
@role_required('super_admin')
def complete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.status == 'confirmed':
        reservation.status = 'completed'
        db.session.commit()
        flash('Reservation marked as completed.', 'success')
    else:
        flash('Only confirmed reservations can be marked as completed.', 'error')
    return redirect(url_for('admin.view_reservation', reservation_id=reservation.id))

# --- Order Management ---

@admin_bp.route('/orders')
@role_required('super_admin')
def list_orders():
    restaurant_id = request.args.get('restaurant_id', type=int)
    status = request.args.get('status', '')
    date_str = request.args.get('date', '')
    
    query = Order.query
    
    if restaurant_id:
        query = query.filter_by(restaurant_id=restaurant_id)
    if status:
        query = query.filter_by(status=status)
    if date_str:
        try:
            from datetime import timedelta
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            next_day = filter_date + timedelta(days=1)
            query = query.filter(Order.created_at >= filter_date, Order.created_at < next_day)
        except ValueError:
            pass
            
    orders = query.order_by(Order.created_at.desc()).all()
    restaurants = Restaurant.query.all()
    
    return render_template('admin/orders.html', 
                           orders=orders, 
                           restaurants=restaurants, 
                           current_restaurant=restaurant_id, 
                           current_status=status, 
                           current_date=date_str)

@admin_bp.route('/orders/<int:order_id>')
@role_required('super_admin')
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_view.html', order=order)

@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@role_required('super_admin')
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    valid_transitions = {
        'placed': ['confirmed', 'cancelled'],
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
        
    return redirect(url_for('admin.view_order', order_id=order.id))
