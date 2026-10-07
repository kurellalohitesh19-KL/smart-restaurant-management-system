from app import db
from datetime import datetime, timezone

class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=False)
    
    reservation_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    number_of_guests = db.Column(db.Integer, nullable=False)
    
    # status: pending, confirmed, cancelled, completed
    status = db.Column(db.String(50), nullable=False, default='pending')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    orders = db.relationship('Order', backref='reservation', lazy=True)

    def __repr__(self):
        return f'<Reservation {self.id} on {self.reservation_date} at {self.start_time}>'
