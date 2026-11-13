"""
API Blueprint - JSON API endpoints for AJAX calls.

Handles:
- Table availability checks
- Reservation creation
- Cart operations (add, update, remove)
- Order placement
- Order status queries

All responses are JSON format.

Implementation will be added in Phases 4-5.
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.table import Table
from app.models.order import Order
from app.services import reservation_service
from datetime import datetime, time, date
import math

api_bp = Blueprint('api', __name__)

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in kilometers between two points on the earth."""
    R = 6371.0 # Radius of earth in kilometers
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

@api_bp.route('/status')
def api_status():
    """API status check."""
    return {
        'status': 'ok',
        'api_version': '1.0',
        'message': 'Smart Restaurant API is running'
    }

@api_bp.route('/restaurants/nearby', methods=['GET'])
def get_nearby_restaurants():
    try:
        lat = float(request.args.get('latitude'))
        lng = float(request.args.get('longitude'))
        radius = float(request.args.get('radius', 10.0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coordinates or radius'}), 400
        
    if not (-90 <= lat <= 90):
        return jsonify({'error': 'Invalid latitude'}), 400
    if not (-180 <= lng <= 180):
        return jsonify({'error': 'Invalid longitude'}), 400
    if radius <= 0 or radius > 1000:
        return jsonify({'error': 'Invalid radius'}), 400

    active_restaurants = Restaurant.query.filter_by(is_active=True).all()
    total_active = len(active_restaurants)
    restaurants_with_coords = [r for r in active_restaurants if r.latitude is not None and r.longitude is not None]
    total_with_coords = len(restaurants_with_coords)

    nearby_restaurants = []
    for r in restaurants_with_coords:
        dist = haversine(lat, lng, r.latitude, r.longitude)
        if dist <= radius:
            # Return safe fields only, including coordinates for map markers
            nearby_restaurants.append({
                'id': r.id,
                'name': r.name,
                'description': r.description or '',
                'address': r.address or '',
                'city': r.city,
                'state': r.state,
                'latitude': r.latitude,
                'longitude': r.longitude,
                'distance': round(dist, 1),
                'image': r.image or '',
                'is_active': r.is_active
            })

    nearby_restaurants.sort(key=lambda x: x['distance'])

    if total_active == 0:
        message = 'No active restaurants are currently available on the platform.'
    elif total_with_coords == 0:
        message = 'Active restaurants exist, but none currently have location coordinates configured.'
    elif len(nearby_restaurants) == 0:
        formatted_radius = int(radius) if radius.is_integer() else radius
        message = f'No restaurants found within {formatted_radius} km. Try increasing the search radius.'
    else:
        message = f'Found {len(nearby_restaurants)} nearby restaurant(s).'

    return jsonify({
        'restaurants': nearby_restaurants,
        'total_active': total_active,
        'total_with_coords': total_with_coords,
        'message': message
    })

DEFAULT_DINING_SLOTS = [
    {"start": "11:00", "end": "12:00", "label": "11:00 AM - 12:00 PM", "meal": "Lunch"},
    {"start": "12:00", "end": "13:00", "label": "12:00 PM - 01:00 PM", "meal": "Lunch"},
    {"start": "13:00", "end": "14:00", "label": "01:00 PM - 02:00 PM", "meal": "Lunch"},
    {"start": "14:00", "end": "15:00", "label": "02:00 PM - 03:00 PM", "meal": "Late Lunch"},
    {"start": "18:00", "end": "19:00", "label": "06:00 PM - 07:00 PM", "meal": "Dinner"},
    {"start": "19:00", "end": "20:00", "label": "07:00 PM - 08:00 PM", "meal": "Dinner"},
    {"start": "20:00", "end": "21:00", "label": "08:00 PM - 09:00 PM", "meal": "Prime Dinner"},
    {"start": "21:00", "end": "22:00", "label": "09:00 PM - 10:00 PM", "meal": "Late Dinner"},
]

@api_bp.route('/restaurants/<int:restaurant_id>/slot-availability', methods=['GET'])
def get_slot_availability(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_active=True).first_or_404()
    
    date_str = request.args.get('date')
    guests = request.args.get('guests', default=2, type=int)
    if guests <= 0:
        guests = 2
        
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
    except (ValueError, TypeError):
        date_obj = datetime.now().date()
        
    candidate_tables = Table.query.filter(
        Table.restaurant_id == restaurant.id,
        Table.status != 'maintenance',
        Table.capacity >= guests
    ).all()
    
    slots_result = []
    now = datetime.now()
    for s in DEFAULT_DINING_SLOTS:
        start_obj = datetime.strptime(s['start'], '%H:%M').time()
        end_obj = datetime.strptime(s['end'], '%H:%M').time()
        
        is_past = False
        if date_obj < now.date():
            is_past = True
        elif date_obj == now.date() and start_obj <= now.time():
            is_past = True
                
        available_count = 0
        if not is_past:
            for t in candidate_tables:
                if not reservation_service.has_overlapping_reservation(t.id, date_obj, start_obj, end_obj):
                    available_count += 1
                    
        slots_result.append({
            'start': s['start'],
            'end': s['end'],
            'label': s['label'],
            'meal': s['meal'],
            'is_available': available_count > 0 and not is_past,
            'is_past': is_past,
            'available_tables': available_count
        })
        
    return jsonify({
        'restaurant_id': restaurant.id,
        'date': date_obj.strftime('%Y-%m-%d'),
        'guests': guests,
        'slots': slots_result
    })

@api_bp.route('/restaurants/<int:restaurant_id>/table-availability', methods=['GET'])
def get_table_availability(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id, is_active=True).first_or_404()
    
    date_str = request.args.get('date')
    start_str = request.args.get('start_time')
    end_str = request.args.get('end_time')
    guests = request.args.get('guests', default=2, type=int)
    if guests <= 0:
        guests = 2
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        start_obj = datetime.strptime(start_str, '%H:%M').time() if start_str else datetime.strptime('18:00', '%H:%M').time()
        end_obj = datetime.strptime(end_str, '%H:%M').time() if end_str else datetime.strptime('19:00', '%H:%M').time()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date or time parameters'}), 400
        
    all_tables = Table.query.filter(
        Table.restaurant_id == restaurant.id,
        Table.status != 'maintenance'
    ).order_by(Table.capacity.asc(), Table.table_number.asc()).all()
    
    tables_result = []
    for t in all_tables:
        has_overlap = reservation_service.has_overlapping_reservation(t.id, date_obj, start_obj, end_obj)
        is_free_slot = not has_overlap
        fits_capacity = (t.capacity >= guests)
        
        if t.capacity <= 2:
            table_type = 'Intimate Duo (1-2 Seats)'
        elif t.capacity <= 4:
            table_type = 'Standard Booth (3-4 Seats)'
        elif t.capacity <= 6:
            table_type = 'Family Dining (5-6 Seats)'
        else:
            table_type = 'Grand Banquet (7+ Seats)'
            
        tables_result.append({
            'id': t.id,
            'table_number': t.table_number,
            'capacity': t.capacity,
            'status': t.status,
            'table_type': table_type,
            'is_available': is_free_slot,
            'fits_capacity': fits_capacity,
            'selectable': is_free_slot and fits_capacity
        })
        
    return jsonify({
        'restaurant_id': restaurant.id,
        'date': date_obj.strftime('%Y-%m-%d'),
        'start_time': start_obj.strftime('%H:%M'),
        'end_time': end_obj.strftime('%H:%M'),
        'guests': guests,
        'tables': tables_result
    })


@api_bp.route('/orders/<int:order_id>/status', methods=['GET'])
def get_order_status(order_id):
    """Return JSON order status with role-based access verification."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401

    order = Order.query.get_or_404(order_id)

    # Check authorization
    is_authorized = False
    if current_user.role == 'super_admin':
        is_authorized = True
    elif current_user.role == 'customer' and order.customer_id == current_user.id:
        is_authorized = True
    elif current_user.role == 'restaurant_owner' and order.restaurant.owner_id == current_user.id:
        is_authorized = True
    elif current_user.role == 'restaurant_staff':
        staff_record = RestaurantStaff.query.filter_by(
            user_id=current_user.id, restaurant_id=order.restaurant_id, is_active=True
        ).first()
        if staff_record:
            is_authorized = True

    if not is_authorized:
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({
        'order_id': order.id,
        'restaurant_id': order.restaurant_id,
        'restaurant_name': order.restaurant.name,
        'status': order.status,
        'is_customer_confirmed': order.is_customer_confirmed,
        'total_amount': float(order.total_amount),
        'items_count': len(order.items),
        'table_id': order.table_id,
        'table_number': order.table.table_number if order.table else None,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'updated_at': order.updated_at.isoformat() if order.updated_at else None,
    })

