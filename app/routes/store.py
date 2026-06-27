from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db, csrf
from app.models.store import Store
from app.models.category import Category
from app.models.product import Product
from app.utils.decorators import vendor_required, store_owner_required
from app.utils.helpers import slugify, save_image, delete_image
import os
import uuid

store_bp = Blueprint('store', __name__, url_prefix='/store')

# ============================================
# RUTA: CREAR TIENDA (SIN vendor_required)
# ============================================
@store_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_store():
    """Crear tienda - Acceso para usuarios logueados"""
    existing_store = Store.query.filter_by(user_id=current_user.id).first()
    if existing_store:
        flash('Ya tienes una tienda creada.', 'info')
        return redirect(url_for('store.dashboard'))
    
    if current_user.role not in ['vendedor', 'admin']:
        flash('Para crear una tienda, debes tener rol de vendedor.', 'warning')
    
    if request.method == 'POST':
        try:
            csrf.protect()
        except Exception as e:
            flash('Error de seguridad. Por favor, recarga la página.', 'error')
            return render_template('store/create.html', categories=Category.query.all())
        
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            whatsapp = request.form.get('whatsapp')
            city = request.form.get('city')
            address = request.form.get('address')
            category_id = request.form.get('category_id') or None
            
            if not all([name, whatsapp, city]):
                flash('Nombre, WhatsApp y ciudad son obligatorios.', 'error')
                return render_template('store/create.html', categories=Category.query.all())
            
            store = Store(
                user_id=current_user.id,
                name=name,
                slug=slugify(name),
                description=description,
                whatsapp=whatsapp,
                city=city,
                address=address,
                category_id=category_id,
                is_active=True,
                is_verified=False
            )
            
            if 'logo' in request.files:
                file = request.files['logo']
                if file and file.filename:
                    filename = save_image(file, f'stores/{current_user.id}')
                    store.logo_url = filename
            
            if 'banner' in request.files:
                file = request.files['banner']
                if file and file.filename:
                    filename = save_image(file, f'stores/{current_user.id}/banner')
                    store.banner_url = filename
            
            db.session.add(store)
            db.session.commit()
            
            if current_user.role != 'admin':
                current_user.role = 'vendedor'
                db.session.commit()
            
            flash('¡Tienda creada exitosamente!', 'success')
            return redirect(url_for('store.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear tienda: {str(e)}', 'error')
    
    categories = Category.query.all()
    return render_template('store/create.html', categories=categories)

# ============================================
# RUTA: DASHBOARD (REQUIERE TIENDA)
# ============================================
@store_bp.route('/dashboard')
@login_required
@vendor_required
def dashboard():
    """Dashboard del vendedor"""
    store = Store.query.filter_by(user_id=current_user.id).first()
    if not store:
        flash('No tienes una tienda. Crea una primero.', 'warning')
        return redirect(url_for('store.create_store'))
    
    # ✅ CORREGIDO: usar len() en lugar de .count()
    total_products = Product.query.filter_by(store_id=store.id).count()
    total_orders = len(store.orders) if store.orders else 0
    
    # Productos recientes
    recent_products = Product.query.filter_by(store_id=store.id).order_by(Product.created_at.desc()).limit(5).all()
    
    # Productos con stock bajo
    low_stock_products = Product.query.filter(
        Product.store_id == store.id,
        Product.stock <= Product.min_stock,
        Product.stock > 0
    ).all()
    
    # Categorías para el modal
    categories = Category.query.all()
    
    return render_template('store/dashboard.html', 
                         store=store, 
                         products=recent_products,
                         total_products=total_products,
                         total_orders=total_orders,
                         low_stock_products=low_stock_products,
                         categories=categories)

# ============================================
# RUTA: EDITAR TIENDA (REQUIERE TIENDA)
# ============================================
@store_bp.route('/edit', methods=['GET', 'POST'])
@login_required
@vendor_required
def edit_store():
    """Editar tienda"""
    store = Store.query.filter_by(user_id=current_user.id).first()
    if not store:
        flash('No tienes una tienda.', 'warning')
        return redirect(url_for('store.create_store'))
    
    if request.method == 'POST':
        try:
            csrf.protect()
        except Exception as e:
            flash('Error de seguridad. Por favor, recarga la página.', 'error')
            return render_template('store/edit.html', store=store, categories=Category.query.all())
        
        try:
            store.name = request.form.get('name', store.name)
            store.description = request.form.get('description', store.description)
            store.whatsapp = request.form.get('whatsapp', store.whatsapp)
            store.city = request.form.get('city', store.city)
            store.address = request.form.get('address', store.address)
            store.category_id = request.form.get('category_id', store.category_id) or None
            
            if 'logo' in request.files:
                file = request.files['logo']
                if file and file.filename:
                    if store.logo_url:
                        delete_image(store.logo_url)
                    filename = save_image(file, f'stores/{current_user.id}')
                    store.logo_url = filename
            
            if 'banner' in request.files:
                file = request.files['banner']
                if file and file.filename:
                    if store.banner_url:
                        delete_image(store.banner_url)
                    filename = save_image(file, f'stores/{current_user.id}/banner')
                    store.banner_url = filename
            
            db.session.commit()
            flash('Tienda actualizada correctamente.', 'success')
            return redirect(url_for('store.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'error')
    
    categories = Category.query.all()
    return render_template('store/edit.html', store=store, categories=categories)

# ============================================
# RUTA: VER TIENDA PÚBLICA
# ============================================
@store_bp.route('/<slug>')
def view_store(slug):
    """Ver tienda pública"""
    store = Store.query.filter_by(slug=slug, is_active=True).first_or_404()
    products = Product.query.filter_by(store_id=store.id, is_active=True).all()
    return render_template('store/view.html', store=store, products=products)