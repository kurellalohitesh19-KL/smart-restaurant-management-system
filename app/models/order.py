from app import db
from datetime import datetime, timezone

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'), nullable=True)
    
    # status: placed, confirmed, preparing, ready, served, cancelled
    status = db.Column(db.String(50), nullable=False, default='placed')
    is_customer_confirmed = db.Column(db.Boolean, default=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.id} - ${self.total_amount}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<OrderItem {self.id} (Qty: {self.quantity})>'
