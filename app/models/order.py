from app.extensions import db
from datetime import datetime
import uuid

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id = db.Column(db.String(36), db.ForeignKey('stores.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pendiente')
    subtotal = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)
    shipping_address = db.Column(db.String(200))
    shipping_city = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)
    
    # Relaciones
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
    
    def get_status_label(self):
        status_map = {
            'pendiente': 'Pendiente',
            'confirmado': 'Confirmado',
            'enviado': 'Enviado',
            'entregado': 'Entregado',
            'cancelado': 'Cancelado'
        }
        return status_map.get(self.status, self.status)
    
    def get_status_color(self):
        color_map = {
            'pendiente': 'warning',
            'confirmado': 'info',
            'enviado': 'primary',
            'entregado': 'success',
            'cancelado': 'danger'
        }
        return color_map.get(self.status, 'secondary')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'status': self.status,
            'status_label': self.get_status_label(),
            'subtotal': self.subtotal,
            'shipping_cost': self.shipping_cost,
            'discount': self.discount,
            'total': self.total,
            'shipping_address': self.shipping_address,
            'shipping_city': self.shipping_city,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<OrderItem {self.product_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price,
            'subtotal': self.subtotal
        }