from app.extensions import db
from datetime import datetime
import uuid

class Follower(db.Model):
    __tablename__ = 'followers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    store_id = db.Column(db.String(36), db.ForeignKey('stores.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'store_id', name='unique_user_store'),)
    
    def __repr__(self):
        return f'<Follower {self.user_id} - {self.store_id}>'