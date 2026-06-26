from app.extensions import db
from datetime import datetime
import uuid

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id = db.Column(db.String(36), db.ForeignKey('stores.id'), nullable=False)
    category_id = db.Column(db.String(36), db.ForeignKey('categories.id'))
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    images = db.Column(db.JSON, default=[])
    stock = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    rating_avg = db.Column(db.Float, default=0)
    rating_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    sold_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='product', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def get_price_with_discount(self):
        return self.discount_price if self.discount_price and self.discount_price < self.price else self.price
    
    def get_discount_percentage(self):
        if self.discount_price and self.discount_price < self.price:
            return round((1 - self.discount_price / self.price) * 100)
        return 0
    
    def is_in_stock(self):
        return self.stock > 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'price': self.price,
            'discount_price': self.discount_price,
            'description': self.description,
            'image_url': self.image_url,
            'images': self.images,
            'stock': self.stock,
            'min_stock': self.min_stock,
            'is_featured': self.is_featured,
            'rating_avg': self.rating_avg,
            'rating_count': self.rating_count,
            'sold_count': self.sold_count,
            'store': self.store.to_dict() if self.store else None,
            'category': self.category.name if self.category else None
        }