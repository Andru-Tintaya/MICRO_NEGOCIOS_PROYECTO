from app.extensions import db
from flask_login import UserMixin
from datetime import datetime
import uuid

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(100), unique=True, nullable=False)
    whatsapp = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='cliente')  # cliente, vendedor, admin
    avatar_url = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    two_factor_secret = db.Column(db.String(255))
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.DateTime)
    preferred_language = db.Column(db.String(5), default='es')
    theme = db.Column(db.String(10), default='light')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    store = db.relationship('Store', backref='owner', uselist=False, lazy=True)
    # products = db.relationship('Product', backref='seller', lazy=True)  # ELIMINADA
    reviews = db.relationship('Review', backref='author', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    followers = db.relationship('Follower', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.full_name}>'
    
    def get_id(self):
        return str(self.id)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_vendor(self):
        return self.role == 'vendedor'
    
    def is_customer(self):
        return self.role == 'cliente'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'whatsapp': self.whatsapp,
            'full_name': self.full_name,
            'role': self.role,
            'avatar_url': self.avatar_url,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }