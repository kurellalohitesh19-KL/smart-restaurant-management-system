from app import db
from datetime import datetime, timezone
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # role can be: customer, restaurant_owner, restaurant_staff, super_admin
    role = db.Column(db.String(50), nullable=False, default='customer', index=True)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    owned_restaurants = db.relationship('Restaurant', backref='owner', lazy=True, foreign_keys='Restaurant.owner_id')
    staff_roles = db.relationship('RestaurantStaff', backref='user', lazy=True)
    reservations = db.relationship('Reservation', backref='customer', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)
    interacted_restaurants = db.relationship('CustomerRestaurant', backref='customer', lazy=True)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
