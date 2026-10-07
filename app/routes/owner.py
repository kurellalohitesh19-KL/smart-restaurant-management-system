from flask import Blueprint
from app.utils import role_required

owner_bp = Blueprint('owner', __name__)

@owner_bp.route('/dashboard')
@role_required('restaurant_owner')
def dashboard():
    """Owner dashboard. Protected for restaurant_owner role."""
    return {'message': 'Owner dashboard - protected'}
