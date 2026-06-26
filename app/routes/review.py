from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.review import Review
from app.models.product import Product
from app.models.store import Store

review_bp = Blueprint('review', __name__, url_prefix='/reviews')

@review_bp.route('/product/<product_id>')
def product_reviews(product_id):
    reviews = Review.query.filter_by(product_id=product_id).order_by(
        Review.created_at.desc()
    ).all()
    
    return render_template('review/list.html', reviews=reviews, product_id=product_id)

@review_bp.route('/create', methods=['POST'])
@login_required
def create():
    product_id = request.form.get('product_id')
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    if not product_id or not rating:
        flash('Producto y calificación son obligatorios', 'error')
        return redirect(request.referrer or url_for('index'))
    
    product = Product.query.get(product_id)
    if not product:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('index'))
    
    existing = Review.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing:
        flash('Ya has reseñado este producto', 'warning')
        return redirect(request.referrer or url_for('index'))
    
    review = Review(
        user_id=current_user.id,
        product_id=product_id,
        store_id=product.store_id,
        rating=int(rating),
        comment=comment
    )
    
    db.session.add(review)
    db.session.commit()
    
    # Actualizar rating del producto
    product_reviews = Review.query.filter_by(product_id=product_id).all()
    if product_reviews:
        product.rating_avg = sum(r.rating for r in product_reviews) / len(product_reviews)
        product.rating_count = len(product_reviews)
        db.session.commit()
    
    # Actualizar rating de la tienda
    store_reviews = Review.query.filter_by(store_id=product.store_id).all()
    if store_reviews:
        store = Store.query.get(product.store_id)
        store.rating_avg = sum(r.rating for r in store_reviews) / len(store_reviews)
        store.rating_count = len(store_reviews)
        db.session.commit()
    
    flash('Reseña publicada exitosamente', 'success')
    return redirect(request.referrer or url_for('index'))