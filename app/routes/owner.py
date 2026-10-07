from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils import role_required
from app import db
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem
from app.models.user import User

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
