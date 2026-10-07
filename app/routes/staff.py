from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils import role_required
from app import db
from app.models.restaurant import RestaurantStaff
from app.models.table import Table

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

# --- Table Management ---

@staff_bp.route('/tables')
@role_required('restaurant_staff')
def list_tables():
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)
        
    tables = Table.query.filter_by(restaurant_id=staff_record.restaurant_id).all()
    return render_template('staff/tables.html', tables=tables, restaurant=staff_record.restaurant)

@staff_bp.route('/tables/<int:table_id>/status', methods=['POST'])
@role_required('restaurant_staff')
def update_table_status(table_id):
    staff_record = RestaurantStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_record:
        abort(403)
        
    table = Table.query.filter_by(id=table_id, restaurant_id=staff_record.restaurant_id).first_or_404()
    
    status = request.form.get('status')
    valid_statuses = ['available', 'occupied', 'maintenance']
    
    if status not in valid_statuses:
        flash("Invalid status selected. Staff can only set to available, occupied, or maintenance.", "danger")
        return redirect(url_for('staff.list_tables'))
        
    table.status = status
    db.session.commit()
    flash("Table status updated successfully.", "success")
    return redirect(url_for('staff.list_tables'))
