from app.extensions import db
from datetime import datetime
import uuid

class Store(db.Model):
    __tablename__ = 'stores'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    whatsapp = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200))
    logo_url = db.Column(db.String(255))
    banner_url = db.Column(db.String(255))
    category_id = db.Column(db.String(36), db.ForeignKey('categories.id'))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    rating_avg = db.Column(db.Float, default=0)
    rating_count = db.Column(db.Integer, default=0)
    followers_count = db.Column(db.Integer, default=0)
    products_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    products = db.relationship('Product', backref='store', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='store', lazy=True)
    orders = db.relationship('Order', backref='store', lazy=True)
    followers = db.relationship('Follower', backref='store', lazy=True)
    
    def __repr__(self):
        return f'<Store {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'whatsapp': self.whatsapp,
            'city': self.city,
            'logo_url': self.logo_url,
            'banner_url': self.banner_url,
            'rating_avg': self.rating_avg,
            'followers_count': self.followers_count,
            'products_count': self.products_count
        }