from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.store import Store
from app.models.product import Product
from app.models.order import Order
from app.models.review import Review
from app.utils.decorators import admin_required
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Estadísticas generales
    total_users = User.query.count()
    total_stores = Store.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_reviews = Review.query.count()
    
    # Usuarios nuevos (últimos 7 días)
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users = User.query.filter(User.created_at >= week_ago).count()
    
    # Órdenes por estado
    orders_by_status = {}
    for status in ['pendiente', 'confirmado', 'enviado', 'entregado', 'cancelado']:
        orders_by_status[status] = Order.query.filter_by(status=status).count()
    
    # Ventas del mes
    month_ago = datetime.utcnow() - timedelta(days=30)
    monthly_sales = db.session.query(db.func.sum(Order.total)).filter(
        Order.created_at >= month_ago,
        Order.status == 'entregado'
    ).scalar() or 0
    
    # Productos más vendidos
    top_products = Product.query.order_by(Product.sold_count.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_stores=total_stores,
        total_products=total_products,
        total_orders=total_orders,
        total_reviews=total_reviews,
        new_users=new_users,
        orders_by_status=orders_by_status,
        monthly_sales=monthly_sales,
        top_products=top_products
    )

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'Usuario {"activado" if user.is_active else "desactivado"} correctamente', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<user_id>/role', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role in ['cliente', 'vendedor', 'admin']:
        user.role = new_role
        db.session.commit()
        flash('Rol actualizado correctamente', 'success')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/stores')
@login_required
@admin_required
def stores():
    stores = Store.query.order_by(Store.created_at.desc()).all()
    return render_template('admin/stores.html', stores=stores)

@admin_bp.route('/stores/<store_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_store(store_id):
    store = Store.query.get_or_404(store_id)
    store.is_active = not store.is_active
    store.is_verified = store.is_active
    db.session.commit()
    flash(f'Tienda {"verificada" if store.is_active else "desactivada"}', 'success')
    return redirect(url_for('admin.stores'))

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    return render_template('admin/reports.html')