from flask import Flask, redirect, url_for, flash, render_template
from flask_login import current_user
from flask_wtf.csrf import CSRFError
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
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('El token de seguridad ha expirado. Por favor, recarga la página.', 'error')
        return redirect(url_for('auth.login'))
    
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
    app.register_blueprint(order.order_bp, url_prefix='/orders')
    app.register_blueprint(favorite.favorite_bp, url_prefix='/favorite')
    app.register_blueprint(follower.follower_bp, url_prefix='/follower')
    app.register_blueprint(notification.notification_bp, url_prefix='/notification')
    app.register_blueprint(admin.admin_bp, url_prefix='/admin')
    app.register_blueprint(api.api_bp, url_prefix='/api')
    
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # ============================================
    # ✅ RUTA PRINCIPAL CORREGIDA
    # ============================================
    @app.route('/')
    def index():
        from app.models.product import Product
        from app.models.category import Category
        from app.models.store import Store
        
        # ✅ Obtener productos destacados (activos y con flag is_featured)
        featured_products = Product.query.filter_by(
            is_active=True, 
            is_featured=True
        ).limit(8).all()
        
        # ✅ Si no hay destacados, mostrar los más recientes
        if not featured_products:
            featured_products = Product.query.filter_by(
                is_active=True
            ).order_by(Product.created_at.desc()).limit(8).all()
        
        categories = Category.query.all()
        stores = Store.query.filter_by(is_active=True).all()
        
        return render_template('index.html', 
                             products=featured_products,
                             featured_products=featured_products,
                             categories=categories, 
                             stores=stores)
    
    with app.app_context():
        try:
            # Crear carpeta instance
            instance_path = os.path.join(app.instance_path)
            if not os.path.exists(instance_path):
                os.makedirs(instance_path)
            
            # Crear carpeta uploads
            upload_path = os.path.join(app.static_folder, 'uploads')
            if not os.path.exists(upload_path):
                os.makedirs(upload_path, exist_ok=True)
                print(f"✅ Carpeta uploads creada: {upload_path}")
            
            # Crear carpeta products
            products_path = os.path.join(upload_path, 'products')
            if not os.path.exists(products_path):
                os.makedirs(products_path, exist_ok=True)
                print(f"✅ Carpeta products creada: {products_path}")
            
            db.create_all()
            print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error al crear carpetas/base de datos: {e}")
    
    return app