from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.favorite import Favorite
from app.models.product import Product

favorite_bp = Blueprint('favorite', __name__, url_prefix='/favorites')

@favorite_bp.route('/')
@login_required
def list():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    products = [f.product for f in favorites if f.product and f.product.is_active]
    return render_template('favorite/list.html', products=products)

@favorite_bp.route('/toggle', methods=['POST'])
@login_required
def toggle():
    product_id = request.json.get('product_id')
    
    if not product_id:
        return jsonify({'error': 'Producto requerido'}), 400
    
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed'})
    else:
        favorite = Favorite(
            user_id=current_user.id,
            product_id=product_id
        )
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'success': True, 'action': 'added'})