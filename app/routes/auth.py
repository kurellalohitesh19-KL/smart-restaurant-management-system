"""
Auth Blueprint - Authentication routes.

Handles:
- User registration (Customer, Restaurant Owner)
- Login / Logout
- Profile management

Implementation will be added in Phase 2.
"""

from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    """Login page. Implementation in Phase 2."""
    return render_template('base.html')


@auth_bp.route('/register')
def register():
    """Registration page. Implementation in Phase 2."""
    return render_template('base.html')
