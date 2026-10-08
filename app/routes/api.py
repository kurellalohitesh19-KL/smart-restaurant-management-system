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
from app.models.restaurant import Restaurant
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

    restaurants = Restaurant.query.filter_by(is_active=True).all()
    nearby_restaurants = []

    for r in restaurants:
        if r.latitude is not None and r.longitude is not None:
            dist = haversine(lat, lng, r.latitude, r.longitude)
            if dist <= radius:
                # Return safe fields only
                nearby_restaurants.append({
                    'id': r.id,
                    'name': r.name,
                    'address': r.address or '',
                    'city': r.city,
                    'state': r.state,
                    'distance': round(dist, 1),
                    'image': r.image or '',
                    'is_active': r.is_active
                })

    nearby_restaurants.sort(key=lambda x: x['distance'])
    return jsonify({'restaurants': nearby_restaurants})
