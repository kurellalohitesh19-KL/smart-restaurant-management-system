from flask import Blueprint, render_template
from flask_login import login_required
from app.utils import role_required

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def home():
    """Customer landing page."""
    return {'message': 'Customer Area (or public home) - placeholder'}
    
@customer_bp.route('/dashboard')
@role_required('customer')
def dashboard():
    """Customer private dashboard."""
    return {'message': 'Customer private dashboard - Phase 5 placeholder'}
