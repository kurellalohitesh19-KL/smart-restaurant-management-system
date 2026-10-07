"""
Smart Restaurant Management System - Utilities Package.
"""
from functools import wraps
from flask import flash, redirect, abort, url_for
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to restrict access to users with specific roles.
    Multiple roles can be specified: @role_required('admin', 'owner')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                from flask import url_for
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                abort(403) # Forbidden access
            return f(*args, **kwargs)
        return decorated_function
    return decorator
