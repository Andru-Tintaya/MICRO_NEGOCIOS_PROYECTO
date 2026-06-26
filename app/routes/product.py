from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Product, Store, Category  # <-- CAMBIADO
from app.utils.decorators import vendor_required
from app.utils.helpers import slugify, save_image, delete_image
import os
import uuid

product_bp = Blueprint('product', __name__, url_prefix='/product')

@product_bp.route('/list')
def list():
    products = Product.query.filter_by(is_active=True).all()
    return render_template('product/list.html', products=products)

@product_bp.route('/create', methods=['GET', 'POST'])
@login_required
@vendor_required
def create():
    store = Store.query.filter_by(user_id=current_user.id).first()
    
    if not store:
        flash('Primero debes crear tu tienda', 'warning')
        return redirect(url_for('store.create'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            price = request.form.get('price')
            discount_price = request.form.get('discount_price')
            description = request.form.get('description')
            stock = request.form.get('stock', 0)
            min_stock = request.form.get('min_stock', 0)
            category_id = request.form.get('category_id')
            is_featured = request.form.get('is_featured') == 'on'
            
            if not all([name, price]):
                flash('Nombre y precio son obligatorios', 'error')
                return render_template('product/create.html', store=store, categories=Category.query.all())
            
            product = Product(
                store_id=store.id,
                category_id=category_id,
                name=name,
                slug=slugify(name),
                price=float(price),
                discount_price=float(discount_price) if discount_price else None,
                description=description,
                stock=int(stock),
                min_stock=int(min_stock) if min_stock else 0,
                is_featured=is_featured,
                is_active=True
            )
            
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    filename = save_image(file, f'products/{store.id}')
                    product.image_url = filename
            
            if 'images[]' in request.files:
                files = request.files.getlist('images[]')
                image_urls = []
                for file in files:
                    if file and file.filename:
                        filename = save_image(file, f'products/{store.id}/gallery')
                        image_urls.append(filename)
                product.images = image_urls
            
            db.session.add(product)
            db.session.commit()
            
            store.products_count = Product.query.filter_by(store_id=store.id).count()
            db.session.commit()
            
            flash('Producto creado exitosamente', 'success')
            return redirect(url_for('store.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear producto: {str(e)}', 'error')
    
    categories = Category.query.all()
    return render_template('product/create.html', store=store, categories=categories)

@product_bp.route('/edit/<product_id>', methods=['GET', 'POST'])
@login_required
@vendor_required
def edit(product_id):
    store = Store.query.filter_by(user_id=current_user.id).first()
    
    if not store:
        flash('No tienes una tienda', 'warning')
        return redirect(url_for('store.create'))
    
    product = Product.query.get_or_404(product_id)
    
    if product.store_id != store.id:
        flash('No tienes permiso para editar este producto', 'error')
        return redirect(url_for('store.dashboard'))
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name', product.name)
            product.price = float(request.form.get('price', product.price))
            product.discount_price = float(request.form.get('discount_price')) if request.form.get('discount_price') else None
            product.description = request.form.get('description', product.description)
            product.stock = int(request.form.get('stock', product.stock))
            product.min_stock = int(request.form.get('min_stock', product.min_stock))
            product.category_id = request.form.get('category_id', product.category_id)
            product.is_featured = request.form.get('is_featured') == 'on'
            product.is_active = request.form.get('is_active') == 'on'
            
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    if product.image_url:
                        delete_image(product.image_url)
                    filename = save_image(file, f'products/{store.id}')
                    product.image_url = filename
            
            if 'images[]' in request.files:
                files = request.files.getlist('images[]')
                image_urls = product.images or []
                for file in files:
                    if file and file.filename:
                        filename = save_image(file, f'products/{store.id}/gallery')
                        image_urls.append(filename)
                product.images = image_urls
            
            db.session.commit()
            flash('Producto actualizado correctamente', 'success')
            return redirect(url_for('store.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'error')
    
    categories = Category.query.all()
    return render_template('product/edit.html', product=product, store=store, categories=categories)

@product_bp.route('/delete/<product_id>', methods=['POST'])
@login_required
@vendor_required
def delete(product_id):
    store = Store.query.filter_by(user_id=current_user.id).first()
    
    if not store:
        return jsonify({'error': 'No tienes una tienda'}), 403
    
    product = Product.query.get_or_404(product_id)
    
    if product.store_id != store.id:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        if product.image_url:
            delete_image(product.image_url)
        
        if product.images:
            for img in product.images:
                delete_image(img)
        
        db.session.delete(product)
        db.session.commit()
        
        store.products_count = Product.query.filter_by(store_id=store.id).count()
        db.session.commit()
        
        flash('Producto eliminado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    
    return redirect(url_for('store.dashboard'))

@product_bp.route('/detail/<slug>')
def detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    product.views_count += 1
    db.session.commit()
    
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    return render_template(
        'product/detail.html',
        product=product,
        related_products=related_products
    )