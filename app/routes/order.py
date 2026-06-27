from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.store import Store
from app.models.notification import Notification
from app.utils.decorators import vendor_required, customer_required
from app.services.notification import send_order_notification
import uuid
from datetime import datetime

order_bp = Blueprint('order', __name__, url_prefix='/orders')

@order_bp.route('/')
@login_required
def list():
    if current_user.is_admin():
        orders = Order.query.order_by(Order.created_at.desc()).all()
    elif current_user.is_vendor():
        store = Store.query.filter_by(user_id=current_user.id).first()
        if store:
            orders = Order.query.filter_by(store_id=store.id).order_by(Order.created_at.desc()).all()
        else:
            orders = []
    else:
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    return render_template('order/list.html', orders=orders)

@order_bp.route('/cart', methods=['GET'])
@login_required
def view_cart():
    """Ver el carrito de compras"""
    return render_template('order/cart.html')

@order_bp.route('/<order_id>')
@login_required
def detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Verificar permisos
    store = Store.query.filter_by(user_id=current_user.id).first()
    if not (current_user.is_admin() or 
            order.user_id == current_user.id or 
            (store and order.store_id == store.id)):
        flash('No tienes permiso para ver este pedido', 'error')
        return redirect(url_for('order.list'))
    
    return render_template('order/detail.html', order=order)

@order_bp.route('/create', methods=['POST'])
@login_required
@customer_required
def create():
    try:
        data = request.json
        
        # Crear número de orden
        order_number = f"MZ-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"
        
        # Calcular totales
        items = data.get('items', [])
        subtotal = sum(item['price'] * item['quantity'] for item in items)
        shipping_cost = data.get('shipping_cost', 0)
        discount = data.get('discount', 0)
        total = subtotal + shipping_cost - discount
        
        # Crear orden
        order = Order(
            store_id=data['store_id'],
            user_id=current_user.id,
            order_number=order_number,
            status='pendiente',
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            discount=discount,
            total=total,
            shipping_address=data.get('shipping_address'),
            shipping_city=data.get('shipping_city'),
            notes=data.get('notes')
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Crear items
        for item_data in items:
            product = Product.query.get(item_data['product_id'])
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                price=item_data['price'],
                subtotal=item_data['price'] * item_data['quantity']
            )
            db.session.add(order_item)
            
            # Actualizar stock
            if product:
                product.stock -= item_data['quantity']
                product.sold_count += item_data['quantity']
        
        db.session.commit()
        
        # Notificar al vendedor
        store = Store.query.get(data['store_id'])
        if store:
            notification = Notification(
                user_id=store.user_id,
                type='order',
                title='¡Nuevo pedido!',
                message=f'Has recibido un nuevo pedido #{order_number}',
                link=f'/orders/{order.id}'
            )
            db.session.add(notification)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': order.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@order_bp.route('/<order_id>/status', methods=['POST'])
@login_required
@vendor_required
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    store = Store.query.filter_by(user_id=current_user.id).first()
    
    if not store or order.store_id != store.id:
        flash('No tienes permiso para modificar este pedido', 'error')
        return redirect(url_for('order.list'))
    
    new_status = request.form.get('status')
    
    if new_status in ['pendiente', 'confirmado', 'enviado', 'entregado', 'cancelado']:
        order.status = new_status
        
        if new_status == 'entregado':
            order.delivered_at = datetime.utcnow()
        
        db.session.commit()
        
        # Notificar al cliente
        notification = Notification(
            user_id=order.user_id,
            type='order',
            title=f'Pedido #{order.order_number}',
            message=f'Tu pedido ha sido {order.get_status_label().lower()}',
            link=f'/orders/{order.id}'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Estado del pedido actualizado', 'success')
    
    return redirect(url_for('order.detail', order_id=order.id))