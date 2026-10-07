from app import db
from datetime import datetime, timezone

class Restaurant(db.Model):
    __tablename__ = 'restaurants'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    staff = db.relationship('RestaurantStaff', backref='restaurant', lazy=True)
    tables = db.relationship('Table', backref='restaurant', lazy=True)
    menu_categories = db.relationship('MenuCategory', backref='restaurant', lazy=True)
    menu_items = db.relationship('MenuItem', backref='restaurant', lazy=True)
    reservations = db.relationship('Reservation', backref='restaurant', lazy=True)
    orders = db.relationship('Order', backref='restaurant', lazy=True)
    customers = db.relationship('CustomerRestaurant', backref='restaurant', lazy=True)

    def __repr__(self):
        return f'<Restaurant {self.name}>'


class RestaurantStaff(db.Model):
    __tablename__ = 'restaurant_staff'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    designation = db.Column(db.String(100), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'restaurant_id', name='uq_staff_user_restaurant'),
    )

    def __repr__(self):
        return f'<RestaurantStaff {self.user_id} @ {self.restaurant_id}>'


class CustomerRestaurant(db.Model):
    __tablename__ = 'customer_restaurant'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    
    first_interaction = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_interaction = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('customer_id', 'restaurant_id', name='uq_customer_restaurant'),
    )

    def __repr__(self):
        return f'<CustomerRestaurant {self.customer_id} -> {self.restaurant_id}>'
