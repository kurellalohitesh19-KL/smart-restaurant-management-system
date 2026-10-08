"""
Smart Restaurant Management and Ordering System

Flask Application Factory Package.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions (not bound to app yet)
db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name='development'):
    """
    Application factory for the Smart Restaurant Management System.

    Args:
        config_name: Configuration to use ('development', 'production', 'testing').

    Returns:
        Flask application instance.
    """
    from config import config as app_config

    app = Flask(__name__)
    app.config.from_object(app_config[config_name])

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)

    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # -------------------------------------------------
    # Register Blueprints (6 total)
    # -------------------------------------------------
    from app.routes.auth import auth_bp
    from app.routes.customer import customer_bp
    from app.routes.owner import owner_bp
    from app.routes.staff import staff_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(owner_bp, url_prefix='/owner')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # -------------------------------------------------
    # Health Check Route
    # -------------------------------------------------
    @app.route('/health')
    def health_check():
        return {
            'status': 'ok',
            'application': 'Smart Restaurant Management System'
        }

    return app
