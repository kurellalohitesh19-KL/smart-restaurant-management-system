from app import db
from datetime import datetime, timezone

class Table(db.Model):
    __tablename__ = 'tables'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    table_number = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=2)
    
    # status: available, reserved, occupied, maintenance
    status = db.Column(db.String(50), nullable=False, default='available')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    reservations = db.relationship('Reservation', backref='table', lazy=True)
    orders = db.relationship('Order', backref='table', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('restaurant_id', 'table_number', name='uq_restaurant_table_number'),
    )

    def __repr__(self):
        return f'<Table {self.table_number} (Capacity: {self.capacity})>'
