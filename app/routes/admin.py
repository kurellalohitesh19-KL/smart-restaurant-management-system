from flask import Blueprint
from app.utils import role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@role_required('super_admin')
def dashboard():
    """Super Admin dashboard. Protected for super_admin role."""
    return {'message': 'Super Admin dashboard - protected'}
