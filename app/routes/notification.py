from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.notification import Notification

notification_bp = Blueprint('notification', __name__, url_prefix='/notifications')

@notification_bp.route('/')
@login_required
def list():
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    return render_template('notification/list.html', notifications=notifications)

@notification_bp.route('/unread')
@login_required
def unread_count():
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'count': count})

@notification_bp.route('/<notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@notification_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    return jsonify({'success': True})