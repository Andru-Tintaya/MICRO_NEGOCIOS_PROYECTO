from flask import Flask, redirect, url_for, render_template
from flask_login import current_user
from app.extensions import db, login_manager, csrf, mail
from app.config import DevelopmentConfig, ProductionConfig
import os
from dotenv import load_dotenv

# Cargamos .env al inicio para asegurar que las variables estén disponibles
load_dotenv()

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Configuración
    if config_class:
        app.config.from_object(config_class)
    else:
        env = os.environ.get('FLASK_ENV', 'development')
        if env == 'production':
            app.config.from_object(ProductionConfig)
        else:
            app.config.from_object(DevelopmentConfig)
    
    # 🔍 Imprimimos la URL de la base de datos para depurar
    print("🔍 DATABASE_URL:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    
    # Configurar login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder.'
    login_manager.login_message_category = 'warning'
    
    # Registrar blueprints
    from app.routes import (
        auth, store, product, category, review, 
        order, favorite, follower, notification, admin, api
    )
    
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(store.store_bp)
    app.register_blueprint(product.product_bp)
    app.register_blueprint(category.category_bp)
    app.register_blueprint(review.review_bp)
    app.register_blueprint(order.order_bp)
    app.register_blueprint(favorite.favorite_bp)
    app.register_blueprint(follower.follower_bp)
    app.register_blueprint(notification.notification_bp)
    app.register_blueprint(admin.admin_bp, url_prefix='/admin')
    app.register_blueprint(api.api_bp, url_prefix='/api')
    
    # Cargar usuario
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # =============================================
    # 🏠 RUTA PRINCIPAL (RAÍZ)
    # =============================================
    @app.route('/')
    def index():
        """Página principal - Redirige al login o al dashboard según sesión"""
        if current_user.is_authenticated:
            # Si el usuario está logueado, redirige al dashboard de la tienda
            return redirect(url_for('store.dashboard'))
        else:
            # Si no está logueado, redirige al login
            return redirect(url_for('auth.login'))
    
    # =============================================
    # 📄 OPCIONAL: Página de inicio personalizada
    # Descomenta esta función si quieres una página de inicio
    # en lugar de redirigir al login
    # =============================================
    # @app.route('/')
    # def index():
    #     """Página principal con landing page"""
    #     if current_user.is_authenticated:
    #         return redirect(url_for('store.dashboard'))
    #     return render_template('index.html')
    
    # Crear tablas (con manejo de errores)
    with app.app_context():
        try:
            # Verificar que la carpeta instance existe
            instance_path = os.path.join(app.instance_path)
            if not os.path.exists(instance_path):
                os.makedirs(instance_path)
                print(f"📁 Creada carpeta: {instance_path}")
            
            db.create_all()
            print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error al crear la base de datos: {e}")
            print("   Verifica que la ruta tenga permisos de escritura.")
    
    return app