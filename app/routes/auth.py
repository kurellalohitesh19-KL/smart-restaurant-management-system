"""
Auth Blueprint - Authentication routes.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user.role)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been disabled.', 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            flash('Logged in successfully!', 'success')
            
            # Redirect to intended page or role dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect_based_on_role(user.role)
            
        flash('Invalid email or password.', 'danger')
        
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user.role)
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not name or not email or not password:
            flash('Please fill out all required fields.', 'warning')
            return redirect(url_for('auth.register'))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email address already registered.', 'danger')
            return redirect(url_for('auth.register'))
            
        if phone and User.query.filter_by(phone=phone).first():
            flash('Phone number already registered.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Create new customer user
        new_user = User(
            name=name,
            email=email,
            phone=phone,
            role='customer'
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

def redirect_based_on_role(role):
    if role == 'customer':
        return redirect(url_for('customer.dashboard'))
    elif role == 'restaurant_owner':
        return redirect(url_for('owner.dashboard'))
    elif role == 'restaurant_staff':
        return redirect(url_for('staff.dashboard'))
    elif role == 'super_admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))
