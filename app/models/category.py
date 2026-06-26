from app.extensions import db
from datetime import datetime
import uuid

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    icon = db.Column(db.String(50))
    description = db.Column(db.String(200))
    parent_id = db.Column(db.String(36), db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    products = db.relationship('Product', backref='category', lazy=True)
    stores = db.relationship('Store', backref='category', lazy=True)
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'