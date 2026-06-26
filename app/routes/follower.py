from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.follower import Follower
from app.models.store import Store

follower_bp = Blueprint('follower', __name__, url_prefix='/followers')

@follower_bp.route('/toggle', methods=['POST'])
@login_required
def toggle():
    store_id = request.json.get('store_id')
    
    if not store_id:
        return jsonify({'error': 'Tienda requerida'}), 400
    
    follower = Follower.query.filter_by(
        user_id=current_user.id,
        store_id=store_id
    ).first()
    
    if follower:
        db.session.delete(follower)
        db.session.commit()
        store = Store.query.get(store_id)
        if store:
            store.followers_count = Follower.query.filter_by(store_id=store_id).count()
            db.session.commit()
        return jsonify({'success': True, 'action': 'unfollowed'})
    else:
        follower = Follower(
            user_id=current_user.id,
            store_id=store_id
        )
        db.session.add(follower)
        db.session.commit()
        store = Store.query.get(store_id)
        if store:
            store.followers_count = Follower.query.filter_by(store_id=store_id).count()
            db.session.commit()
        return jsonify({'success': True, 'action': 'followed'})

@follower_bp.route('/<store_id>')
@login_required
def status(store_id):
    is_following = Follower.query.filter_by(
        user_id=current_user.id,
        store_id=store_id
    ).first() is not None
    
    count = Follower.query.filter_by(store_id=store_id).count()
    
    return jsonify({
        'is_following': is_following,
        'count': count
    })