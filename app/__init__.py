from flask import Flask, redirect, url_for, flash
from flask_login import current_user
from app.extensions import db, login_manager, csrf, mail
from app.config import DevelopmentConfig, ProductionConfig
import os
from dotenv import load_dotenv

load_dotenv()

def create_app(config_class=None):
    app = Flask(__name__)
    
    if config_class:
        app.config.from_object(config_class)
    else:
        env = os.environ.get('FLASK_ENV', 'development')
        if env == 'production':
            app.config.from_object(ProductionConfig)
        else:
            app.config.from_object(DevelopmentConfig)
    
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder.'
    login_manager.login_message_category = 'warning'
    
    # Registrar blueprints
    from app.routes import (
        auth, store, product, category, review, 
        order, favorite, follower, notification, admin, api
    )
    
    app.register_blueprint(auth.auth_bp, url_prefix='/auth')
    app.register_blueprint(store.store_bp, url_prefix='/store')
    app.register_blueprint(product.product_bp, url_prefix='/product')
    app.register_blueprint(category.category_bp, url_prefix='/category')
    app.register_blueprint(review.review_bp, url_prefix='/review')
    app.register_blueprint(order.order_bp, url_prefix='/order')
    app.register_blueprint(favorite.favorite_bp, url_prefix='/favorite')
    app.register_blueprint(follower.follower_bp, url_prefix='/follower')
    app.register_blueprint(notification.notification_bp, url_prefix='/notification')
    app.register_blueprint(admin.admin_bp, url_prefix='/admin')
    app.register_blueprint(api.api_bp, url_prefix='/api')
    
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            from app.models.store import Store
            store = Store.query.filter_by(user_id=current_user.id).first()
            if store:
                return redirect(url_for('store.dashboard', store_id=store.id))
            else:
                flash('Por favor crea tu tienda para comenzar.', 'info')
                return redirect(url_for('store.create_store'))
        else:
            return redirect(url_for('auth.login'))
    
    with app.app_context():
        try:
            instance_path = os.path.join(app.instance_path)
            if not os.path.exists(instance_path):
                os.makedirs(instance_path)
            
            db.create_all()
            print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error al crear la base de datos: {e}")
    
    return app