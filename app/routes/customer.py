from flask import Blueprint, render_template, request, abort
from flask_login import login_required
from app.utils import role_required
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem
from app.models.reservation import Reservation
from app.models.restaurant import CustomerRestaurant
from app.models.order import Order, OrderItem
from app import db
from datetime import datetime, timezone
from flask_login import current_user
from flask import flash, redirect, url_for, session
from app.services import reservation_service

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/dashboard')
@role_required('customer')
def dashboard():
    name_filter = request.args.get('name', '').strip()
    city_filter = request.args.get('city', '').strip()
    category_filter = (request.args.get('category') or request.args.get('cuisine', '')).strip()

    # Query active restaurants
    rest_query = Restaurant.query.filter_by(is_active=True)
    if name_filter:
        rest_query = rest_query.filter(Restaurant.name.ilike(f'%{name_filter}%'))
    if city_filter:
        rest_query = rest_query.filter(Restaurant.city.ilike(f'%{city_filter}%'))
    if category_filter:
        rest_query = rest_query.join(MenuCategory).filter(
            MenuCategory.name.ilike(f'%{category_filter}%'),
            MenuCategory.is_active == True
        )
    restaurants = rest_query.all()

    # Active categories across active restaurants for discovery chips
    categories = db.session.query(MenuCategory.name).join(
        Restaurant, MenuCategory.restaurant_id == Restaurant.id
    ).filter(
        Restaurant.is_active == True,
        MenuCategory.is_active == True
    ).distinct().limit(12).all()
    cuisine_chips = [c[0] for c in categories]

    # Customer's active operations
    upcoming_reservation = Reservation.query.filter(
        Reservation.customer_id == current_user.id,
        Reservation.status.in_(['pending', 'confirmed']),
        Reservation.reservation_date >= datetime.now().date()
    ).order_by(Reservation.reservation_date, Reservation.start_time).first()

    recent_reservations = Reservation.query.filter_by(
        customer_id=current_user.id
    ).order_by(Reservation.created_at.desc()).limit(5).all()

    recent_orders = Order.query.filter_by(
        customer_id=current_user.id
    ).order_by(Order.created_at.desc()).limit(5).all()

    active_orders = Order.query.filter(
        Order.customer_id == current_user.id,
        Order.status.in_(['placed', 'confirmed', 'preparing', 'ready'])
    ).order_by(Order.created_at.desc()).all()

    return render_template(
        'customer/dashboard.html',
        restaurants=restaurants,
        cuisine_chips=cuisine_chips,
        upcoming_reservation=upcoming_reservation,
        recent_reservations=recent_reservations,
        recent_orders=recent_orders,
        active_orders=active_orders,
        current_name=name_filter,
        current_city=city_filter,
        current_category=category_filter
    )

@customer_bp.route('/restaurants')
@role_required('customer')
def list_restaurants():
    query = Restaurant.query.filter_by(is_active=True)
    
    name_filter = request.args.get('name', '').strip()
    city_filter = request.args.get('city', '').strip()
    category_filter = (request.args.get('category') or request.args.get('cuisine', '')).strip()
    
    if name_filter:
        query = query.filter(Restaurant.name.ilike(f'%{name_filter}%'))
    if city_filter:
        query = query.filter(Restaurant.city.ilike(f'%{city_filter}%'))
    if category_filter:
        query = query.join(MenuCategory).filter(
            MenuCategory.name.ilike(f'%{category_filter}%'),
            MenuCategory.is_active == True
        )
        
    restaurants = query.all()
    return render_template(
        'customer/restaurants.html',
        restaurants=restaurants,
        current_name=name_filter,
        current_city=city_filter,
        current_category=category_filter
    )

@customer_bp.route('/profile', methods=['GET', 'POST'])
@role_required('customer')
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()

        if not name:
            flash("Name cannot be empty.", "danger")
        else:
            current_user.name = name
            current_user.phone = phone if phone else None
            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for('customer.profile'))

    order_count = Order.query.filter_by(customer_id=current_user.id).count()
    reservation_count = Reservation.query.filter_by(customer_id=current_user.id).count()
    return render_template(
        'customer/profile.html',
        order_count=order_count,
        reservation_count=reservation_count
    )

@customer_bp.route('/restaurants/<int:restaurant_id>')
@role_required('customer')
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_active=True).first_or_404()
    categories = MenuCategory.query.filter_by(restaurant_id=restaurant.id, is_active=True).all()
    featured_items = MenuItem.query.filter_by(restaurant_id=restaurant.id, is_available=True).limit(6).all()
    available_tables_count = Table.query.filter(
        Table.restaurant_id == restaurant.id,
        Table.status != 'maintenance'
    ).count()
    return render_template(
        'customer/restaurant_detail.html',
        restaurant=restaurant,
        categories=categories,
        featured_items=featured_items,
        available_tables_count=available_tables_count
    )

@customer_bp.route('/restaurants/<int:restaurant_id>/menu')
@role_required('customer')
def restaurant_menu(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_active=True).first_or_404()
    categories = MenuCategory.query.filter_by(restaurant_id=restaurant.id, is_active=True).all()
    return render_template('customer/menu.html', restaurant=restaurant, categories=categories)

@customer_bp.route('/restaurants/<int:restaurant_id>/tables')
@role_required('customer')
def restaurant_tables(restaurant_id):
    """Show tables that are currently available."""
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_active=True).first_or_404()
    tables = Table.query.filter_by(restaurant_id=restaurant.id, status='available').all()
    return render_template('customer/tables.html', restaurant=restaurant, tables=tables)

@customer_bp.route('/restaurants/<int:restaurant_id>/reserve', methods=['GET', 'POST'])
@role_required('customer')
def create_reservation(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_active=True).first_or_404()

    if request.method == 'POST':
        table_id = request.form.get('table_id')
        res_date = request.form.get('reservation_date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        guests = request.form.get('number_of_guests', type=int)

        # --- Parse & validate inputs ---
        try:
            res_date_obj = datetime.strptime(res_date, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
        except (ValueError, TypeError):
            flash('Invalid date or time format.', 'error')
            return redirect(url_for('customer.create_reservation', restaurant_id=restaurant.id))

        if not table_id or not res_date or not start_time_str or not end_time_str or not guests:
            flash('All fields are required.', 'error')
            return redirect(url_for('customer.create_reservation', restaurant_id=restaurant.id))

        if guests <= 0:
            flash('Number of guests must be at least 1.', 'error')
            return redirect(url_for('customer.create_reservation', restaurant_id=restaurant.id))

        if start_time_obj >= end_time_obj:
            flash('Start time must be before end time.', 'error')
            return redirect(url_for('customer.create_reservation', restaurant_id=restaurant.id))

        table = Table.query.filter_by(id=table_id, restaurant_id=restaurant.id).first()
        if not table:
            flash('Invalid table selected.', 'error')
            return redirect(url_for('customer.create_reservation', restaurant_id=restaurant.id))

        if table.status == 'maintenance':
            flash('This table is currently under maintenance.', 'error')
            return redirect(url_for('customer.create_reservation', restaurant_id=restaurant.id))

        if guests > table.capacity:
            flash(f'Number of guests ({guests}) exceeds table capacity ({table.capacity}).', 'error')
            return redirect(url_for('customer.create_reservation', restaurant_id=restaurant.id))

        # --- Concurrency-safe overlap check (server-side) ---
        if reservation_service.has_overlapping_reservation(
            table.id, res_date_obj, start_time_obj, end_time_obj
        ):
            flash('The table is already reserved for the selected time.', 'error')
            return redirect(url_for('customer.create_reservation', restaurant_id=restaurant.id))

        # --- Create and AUTO-CONFIRM the reservation ---
        reservation = Reservation(
            customer_id=current_user.id,
            restaurant_id=restaurant.id,
            table_id=table.id,
            reservation_date=res_date_obj,
            start_time=start_time_obj,
            end_time=end_time_obj,
            number_of_guests=guests,
            status='pending',  # will be overridden below
        )
        db.session.add(reservation)
        db.session.flush()  # get reservation.id before marking table

        # Auto-confirm: no owner approval required
        reservation_service.auto_confirm_new_reservation(reservation)

        # --- Track customer–restaurant interaction ---
        cr = CustomerRestaurant.query.filter_by(
            customer_id=current_user.id, restaurant_id=restaurant.id
        ).first()
        if not cr:
            cr = CustomerRestaurant(customer_id=current_user.id, restaurant_id=restaurant.id)
            db.session.add(cr)
        else:
            cr.last_interaction = datetime.now(timezone.utc)

        db.session.commit()

        flash('Reservation created successfully! Your table has been booked successfully!', 'success')
        return redirect(url_for('customer.reservation_detail', reservation_id=reservation.id))

    tables = Table.query.filter(
        Table.restaurant_id == restaurant.id,
        Table.status != 'maintenance'
    ).all()
    return render_template('customer/reservation_form.html', restaurant=restaurant, tables=tables)

@customer_bp.route('/reservations')
@role_required('customer')
def list_reservations():
    reservations = Reservation.query.filter_by(customer_id=current_user.id).order_by(Reservation.reservation_date.desc(), Reservation.start_time.desc()).all()
    return render_template('customer/reservations.html', reservations=reservations)

@customer_bp.route('/reservations/<int:reservation_id>')
@role_required('customer')
def reservation_detail(reservation_id):
    reservation = Reservation.query.filter_by(id=reservation_id, customer_id=current_user.id).first_or_404()
    return render_template('customer/reservation_detail.html', reservation=reservation)

@customer_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@role_required('customer')
def cancel_reservation(reservation_id):
    reservation = Reservation.query.filter_by(id=reservation_id, customer_id=current_user.id).first_or_404()
    if reservation.status not in ['pending', 'confirmed']:
        flash('Only pending or confirmed reservations can be cancelled.', 'error')
    else:
        # Use service so table.status is released when no other reservation holds it
        reservation_service.cancel_reservation(reservation)
        flash('Reservation cancelled successfully.', 'success')
    return redirect(url_for('customer.list_reservations'))

# --- Cart and Ordering ---

@customer_bp.route('/cart')
@role_required('customer')
def view_cart():
    cart = session.get('cart', {})
    cart_items = {}
    total_amount = 0
    
    for item_id_str, qty in cart.items():
        item = MenuItem.query.get(int(item_id_str))
        if item:
            subtotal = float(item.price) * qty
            cart_items[item_id_str] = {
                'name': item.name,
                'price': float(item.price),
                'quantity': qty,
                'subtotal': subtotal
            }
            total_amount += subtotal
            
    return render_template('customer/cart.html', cart_items=cart_items, total_amount=total_amount)

@customer_bp.route('/cart/add', methods=['POST'])
@role_required('customer')
def add_to_cart():
    menu_item_id = request.form.get('menu_item_id')
    item = MenuItem.query.filter_by(id=menu_item_id, is_available=True).first()
    
    if not item:
        flash("Menu item not found or unavailable.", "danger")
        return redirect(request.referrer or url_for('customer.dashboard'))
        
    restaurant = item.category.restaurant if item.category else None
    if not restaurant or not restaurant.is_active:
        flash("Restaurant is inactive.", "danger")
        return redirect(request.referrer or url_for('customer.dashboard'))
        
    cart = session.get('cart', {})
    cart_restaurant_id = session.get('cart_restaurant_id')
    
    if cart and cart_restaurant_id and cart_restaurant_id != restaurant.id:
        flash("You can only order from one restaurant at a time. Please clear your cart first.", "danger")
        return redirect(request.referrer or url_for('customer.dashboard'))
        
    session['cart_restaurant_id'] = restaurant.id
    item_id_str = str(item.id)
    cart[item_id_str] = cart.get(item_id_str, 0) + 1
    session['cart'] = cart
    session.modified = True
    
    flash("Item added to cart.", "success")
    return redirect(request.referrer or url_for('customer.view_cart'))

@customer_bp.route('/cart/update', methods=['POST'])
@role_required('customer')
def update_cart():
    menu_item_id = request.form.get('menu_item_id')
    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            raise ValueError
    except ValueError:
        flash("Invalid quantity.", "danger")
        return redirect(url_for('customer.view_cart'))
        
    cart = session.get('cart', {})
    if menu_item_id in cart:
        cart[menu_item_id] = quantity
        session['cart'] = cart
        session.modified = True
        flash("Cart updated.", "success")
        
    return redirect(url_for('customer.view_cart'))

@customer_bp.route('/cart/remove', methods=['POST'])
@role_required('customer')
def remove_from_cart():
    menu_item_id = request.form.get('menu_item_id')
    cart = session.get('cart', {})
    
    if menu_item_id in cart:
        del cart[menu_item_id]
        session['cart'] = cart
        
        if not cart:
            session.pop('cart_restaurant_id', None)
            
        session.modified = True
        flash("Item removed from cart.", "success")
        
    return redirect(url_for('customer.view_cart'))

@customer_bp.route('/order/place', methods=['POST'])
@role_required('customer')
def place_order():
    cart = session.get('cart', {})
    cart_restaurant_id = session.get('cart_restaurant_id')
    
    if not cart or not cart_restaurant_id:
        flash("Your cart is empty.", "danger")
        return redirect(url_for('customer.view_cart'))
        
    restaurant = Restaurant.query.filter_by(id=cart_restaurant_id, is_active=True).first()
    if not restaurant:
        flash("Restaurant is inactive or not found.", "danger")
        return redirect(url_for('customer.view_cart'))
        
    order = Order(
        customer_id=current_user.id,
        restaurant_id=restaurant.id,
        status='placed',
        total_amount=0
    )
    db.session.add(order)
    db.session.flush()
    
    total_amount = 0
    
    for item_id_str, qty in cart.items():
        item = MenuItem.query.filter_by(id=int(item_id_str), is_available=True).first()
        if not item or item.category.restaurant_id != restaurant.id:
            db.session.rollback()
            flash("Some items in your cart are no longer available.", "danger")
            return redirect(url_for('customer.view_cart'))
            
        subtotal = float(item.price) * qty
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item.id,
            quantity=qty,
            unit_price=item.price,
            subtotal=subtotal
        )
        db.session.add(order_item)
        total_amount += subtotal
        
    order.total_amount = total_amount
    
    # Update CustomerRestaurant interaction
    cr = CustomerRestaurant.query.filter_by(customer_id=current_user.id, restaurant_id=restaurant.id).first()
    if not cr:
        cr = CustomerRestaurant(customer_id=current_user.id, restaurant_id=restaurant.id)
        db.session.add(cr)
    else:
        cr.last_interaction = datetime.now(timezone.utc)
        
    db.session.commit()
    
    session.pop('cart', None)
    session.pop('cart_restaurant_id', None)
    
    flash("Order placed successfully.", "success")
    return redirect(url_for('customer.list_orders'))

@customer_bp.route('/orders')
@role_required('customer')
def list_orders():
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('customer/orders.html', orders=orders)

@customer_bp.route('/orders/<int:order_id>')
@role_required('customer')
def order_detail(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    
    is_editable = order.status in ['placed', 'confirmed'] and not order.is_customer_confirmed
    
    menu_items = []
    if is_editable:
        # Get available menu items for this restaurant to allow adding new items
        from app.models.menu import MenuItem
        menu_items = MenuItem.query.join(MenuItem.category).filter(
            MenuItem.is_available == True,
            MenuCategory.restaurant_id == order.restaurant_id,
            MenuCategory.is_active == True
        ).all()
        
    return render_template('customer/order_detail.html', order=order, is_editable=is_editable, menu_items=menu_items)

@customer_bp.route('/orders/<int:order_id>/add-item', methods=['POST'])
@role_required('customer')
def order_add_item(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    
    if order.status not in ['placed', 'confirmed'] or order.is_customer_confirmed:
        flash("Order is locked and cannot be modified.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    menu_item_id = request.form.get('menu_item_id')
    quantity = request.form.get('quantity', type=int, default=1)
    
    if quantity < 1:
        flash("Invalid quantity.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    from app.models.menu import MenuItem
    item = MenuItem.query.filter_by(id=menu_item_id, is_available=True).first()
    
    if not item or item.category.restaurant_id != order.restaurant_id:
        flash("Menu item not found or does not belong to this restaurant.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    if not item.category.restaurant.is_active:
        flash("Restaurant is inactive.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    # Check if item already in order
    existing_order_item = next((oi for oi in order.items if oi.menu_item_id == item.id), None)
    
    if existing_order_item:
        existing_order_item.quantity += quantity
        existing_order_item.subtotal = existing_order_item.quantity * existing_order_item.unit_price
    else:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item.id,
            quantity=quantity,
            unit_price=item.price,
            subtotal=item.price * quantity
        )
        db.session.add(order_item)
        order.items.append(order_item)
        
    # Recalculate total
    order.total_amount = sum(oi.subtotal for oi in order.items)
    db.session.commit()
    
    flash("Item added to order.", "success")
    return redirect(url_for('customer.order_detail', order_id=order.id))

@customer_bp.route('/orders/<int:order_id>/update-item', methods=['POST'])
@role_required('customer')
def order_update_item(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    
    if order.status not in ['placed', 'confirmed'] or order.is_customer_confirmed:
        flash("Order is locked and cannot be modified.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    order_item_id = request.form.get('order_item_id')
    quantity = request.form.get('quantity', type=int)
    
    if quantity is None or quantity < 1:
        flash("Invalid quantity.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    order_item = OrderItem.query.filter_by(id=order_item_id, order_id=order.id).first()
    if not order_item:
        flash("Order item not found.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    order_item.quantity = quantity
    order_item.subtotal = order_item.quantity * order_item.unit_price
    
    # Recalculate total
    order.total_amount = sum(oi.subtotal for oi in order.items)
    db.session.commit()
    
    flash("Order item updated.", "success")
    return redirect(url_for('customer.order_detail', order_id=order.id))

@customer_bp.route('/orders/<int:order_id>/remove-item', methods=['POST'])
@role_required('customer')
def order_remove_item(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    
    if order.status not in ['placed', 'confirmed'] or order.is_customer_confirmed:
        flash("Order is locked and cannot be modified.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    order_item_id = request.form.get('order_item_id')
    order_item = OrderItem.query.filter_by(id=order_item_id, order_id=order.id).first()
    
    if not order_item:
        flash("Order item not found.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    if len(order.items) <= 1:
        flash("Cannot remove the last item. Cancel the order instead.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    db.session.delete(order_item)
    order.items.remove(order_item)
    
    # Recalculate total
    order.total_amount = sum(oi.subtotal for oi in order.items)
    db.session.commit()
    
    flash("Order item removed.", "success")
    return redirect(url_for('customer.order_detail', order_id=order.id))

@customer_bp.route('/orders/<int:order_id>/confirm', methods=['POST'])
@role_required('customer')
def order_confirm_final(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    
    if order.status not in ['placed', 'confirmed'] or order.is_customer_confirmed:
        flash("Order is already locked or confirmed.", "danger")
        return redirect(url_for('customer.order_detail', order_id=order.id))
        
    order.is_customer_confirmed = True
    db.session.commit()
    
    flash("Final order confirmed. The restaurant will start preparing soon.", "success")
    return redirect(url_for('customer.order_detail', order_id=order.id))


@customer_bp.route('/orders/<int:order_id>/receipt')
@role_required('customer')
def order_receipt(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    return render_template('customer/receipt.html', order=order, is_internal=False)

