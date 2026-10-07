from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from app.utils import role_required
from app.models.restaurant import RestaurantStaff

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/dashboard')
@role_required('restaurant_staff')
def dashboard():
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        return {'message': 'Staff record not found. Please contact your restaurant owner.'}
        
    restaurant = staff_record.restaurant
    
    return render_template('staff/dashboard.html', 
                           staff_record=staff_record, 
                           restaurant=restaurant)
