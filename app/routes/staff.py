from flask import Blueprint
from app.utils import role_required

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/dashboard')
@role_required('restaurant_staff')
def dashboard():
    """Staff dashboard. Protected for restaurant_staff role."""
    return {'message': 'Staff dashboard - protected'}
