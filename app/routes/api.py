from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.models.product import Product
from app.models.store import Store
from app.models.review import Review
from app.models.favorite import Favorite
from app.models.follower import Follower
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.notification import Notification
from app.utils.decorators import vendor_required, customer_required
from app.utils.helpers import slugify, save_image, delete_image
from datetime import datetime
import uuid
import traceback

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ============================================
# CATEGORÍAS API
# ============================================

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify({
        'success': True,
        'data': [{
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'icon': c.icon,
            'product_count': len(c.products)
        } for c in categories]
    })

# ============================================
# PRODUCTOS API
# ============================================

@api_bp.route('/products', methods=['GET'])
def get_products():
    category_id = request.args.get('category_id')
    store_id = request.args.get('store_id')
    search = request.args.get('search', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort_by', 'created_at')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = Product.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if store_id:
        query = query.filter_by(store_id=store_id)
    
    if search:
        query = query.filter(
            Product.name.ilike(f'%{search}%') | 
            Product.description.ilike(f'%{search}%')
        )
    
    if min_price:
        query = query.filter(Product.price >= min_price)
    
    if max_price:
        query = query.filter(Product.price <= max_price)
    
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'rating':
        query = query.order_by(Product.rating_avg.desc())
    elif sort_by == 'sold':
        query = query.order_by(Product.sold_count.desc())
    else:
        query = query.order_by(Product.created_at.desc())
    
    products = query.limit(limit).offset(offset).all()
    total = query.count()
    
    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in products],
        'total': total,
        'limit': limit,
        'offset': offset
    })

@api_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'success': True,
        'data': product.to_dict()
    })

@api_bp.route('/store/<store_id>/products', methods=['GET'])
@login_required
def get_store_products(store_id):
    """Obtener productos de una tienda específica (para el dashboard)"""
    store = Store.query.get_or_404(store_id)
    
    # Verificar permisos
    if store.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    products = Product.query.filter_by(store_id=store_id).all()
    
    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in products]
    })

# ============================================
# CREAR PRODUCTO (POST)
# ============================================

@api_bp.route('/products', methods=['POST'])
@csrf.exempt
@login_required
def create_product_api():
    print("=" * 50)
    print("📥 RECIBIDA SOLICITUD POST /api/products")
    print("=" * 50)
    
    try:
        store = Store.query.filter_by(user_id=current_user.id).first()
        print(f"👤 Usuario: {current_user.id} - {current_user.full_name}")
        print(f"🏪 Store: {store.id if store else 'No tiene tienda'}")
        
        if not store:
            print("❌ ERROR: Usuario no tiene tienda")
            return jsonify({'success': False, 'error': 'No tienes una tienda. Crea una primero.'}), 400
        
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description', '')
        stock = request.form.get('stock', 0)
        category_id = request.form.get('category_id')
        discount_price = request.form.get('discount_price')
        min_stock = request.form.get('min_stock', 0)
        is_featured = request.form.get('is_featured') == 'on'
        
        print(f"📝 Datos recibidos:")
        print(f"   - Nombre: {name}")
        print(f"   - Precio: {price}")
        print(f"   - Descuento: {discount_price}")
        print(f"   - Stock: {stock}")
        print(f"   - Categoría: {category_id}")
        print(f"   - Destacado: {is_featured}")
        
        if not name:
            return jsonify({'success': False, 'error': 'El nombre del producto es obligatorio'}), 400
        
        if not price:
            return jsonify({'success': False, 'error': 'El precio del producto es obligatorio'}), 400
        
        try:
            price_float = float(price)
        except ValueError:
            return jsonify({'success': False, 'error': 'El precio debe ser un número válido'}), 400
        
        try:
            stock_int = int(stock) if stock else 0
        except ValueError:
            stock_int = 0
        
        # Crear producto
        product = Product(
            store_id=store.id,
            name=name,
            slug=slugify(name),
            price=price_float,
            description=description,
            stock=stock_int,
            is_active=True
        )
        
        if category_id:
            product.category_id = category_id
        
        if discount_price:
            try:
                product.discount_price = float(discount_price)
            except ValueError:
                pass
        
        if min_stock:
            try:
                product.min_stock = int(min_stock)
            except ValueError:
                pass
        
        product.is_featured = is_featured
        
        # Subir imagen
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                print(f"📷 Subiendo imagen: {file.filename}")
                try:
                    filename = save_image(file, f'products/{store.id}')
                    product.image_url = filename
                    print(f"✅ Imagen guardada: {filename}")
                except Exception as img_error:
                    print(f"⚠️ Error al subir imagen: {str(img_error)}")
        
        db.session.add(product)
        db.session.commit()
        print(f"✅ Producto creado con ID: {product.id}")
        
        store.products_count = Product.query.filter_by(store_id=store.id).count()
        db.session.commit()
        print(f"📊 Productos totales en tienda: {store.products_count}")
        print("=" * 50)
        
        return jsonify({
            'success': True,
            'message': 'Producto creado exitosamente',
            'data': product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR EXCEPCIÓN: {str(e)}")
        print(traceback.format_exc())
        print("=" * 50)
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# ACTUALIZAR PRODUCTO (PUT)
# ============================================

@api_bp.route('/products/<product_id>', methods=['PUT'])
@csrf.exempt
@login_required
def update_product_api(product_id):
    print("=" * 50)
    print(f"📥 RECIBIDA SOLICITUD PUT /api/products/{product_id}")
    print("=" * 50)
    
    try:
        product = Product.query.get_or_404(product_id)
        store = Store.query.filter_by(user_id=current_user.id).first()
        
        print(f"👤 Usuario: {current_user.id}")
        print(f"📦 Producto: {product.name} (ID: {product.id})")
        print(f"🏪 Store: {store.id if store else 'No tiene tienda'}")
        
        if not store or product.store_id != store.id:
            print(f"❌ ERROR: Usuario no es dueño del producto")
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        name = request.form.get('name', product.name)
        price = request.form.get('price', product.price)
        description = request.form.get('description', product.description)
        stock = request.form.get('stock', product.stock)
        category_id = request.form.get('category_id', product.category_id)
        discount_price = request.form.get('discount_price')
        min_stock = request.form.get('min_stock', product.min_stock)
        is_active = request.form.get('is_active') == 'on'
        is_featured = request.form.get('is_featured') == 'on'
        
        print(f"📝 Actualizando datos:")
        print(f"   - Nombre: {name}")
        print(f"   - Precio: {price}")
        print(f"   - Stock: {stock}")
        print(f"   - Activo: {is_active}")
        
        product.name = name
        product.price = float(price) if price else product.price
        product.description = description
        product.stock = int(stock) if stock else 0
        product.category_id = category_id
        product.is_active = is_active
        product.is_featured = is_featured
        
        if discount_price:
            try:
                product.discount_price = float(discount_price)
            except ValueError:
                pass
        else:
            product.discount_price = None
        
        if min_stock:
            try:
                product.min_stock = int(min_stock)
            except ValueError:
                pass
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                print(f"📷 Actualizando imagen: {file.filename}")
                if product.image_url:
                    delete_image(product.image_url)
                filename = save_image(file, f'products/{store.id}')
                product.image_url = filename
                print(f"✅ Imagen actualizada: {filename}")
        
        db.session.commit()
        print(f"✅ Producto actualizado correctamente")
        print("=" * 50)
        
        return jsonify({
            'success': True,
            'message': 'Producto actualizado exitosamente',
            'data': product.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR EXCEPCIÓN: {str(e)}")
        print(traceback.format_exc())
        print("=" * 50)
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# ELIMINAR PRODUCTO (DELETE)
# ============================================

@api_bp.route('/products/<product_id>', methods=['DELETE'])
@csrf.exempt
@login_required
def delete_product_api(product_id):
    print("=" * 50)
    print(f"📥 RECIBIDA SOLICITUD DELETE /api/products/{product_id}")
    print("=" * 50)
    
    try:
        product = Product.query.get_or_404(product_id)
        store = Store.query.filter_by(user_id=current_user.id).first()
        
        if not store or product.store_id != store.id:
            print(f"❌ ERROR: Usuario no es dueño del producto")
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
        if product.image_url:
            delete_image(product.image_url)
            print(f"🗑️ Imagen eliminada: {product.image_url}")
        
        db.session.delete(product)
        db.session.commit()
        
        store.products_count = Product.query.filter_by(store_id=store.id).count()
        db.session.commit()
        
        print(f"✅ Producto eliminado correctamente")
        print("=" * 50)
        
        return jsonify({'success': True, 'message': 'Producto eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR EXCEPCIÓN: {str(e)}")
        print(traceback.format_exc())
        print("=" * 50)
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# RESEÑAS API
# ============================================

@api_bp.route('/reviews', methods=['POST'])
@csrf.exempt
@login_required
def create_review():
    try:
        data = request.json
        product_id = data.get('product_id')
        rating = data.get('rating')
        comment = data.get('comment')
        
        if not product_id or not rating:
            return jsonify({'error': 'Producto y calificación son obligatorios'}), 400
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        existing = Review.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Ya has reseñado este producto'}), 400
        
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
        store = Store.query.get(product.store_id)
        if store:
            store_reviews = Review.query.filter_by(store_id=store.id).all()
            if store_reviews:
                store.rating_avg = sum(r.rating for r in store_reviews) / len(store_reviews)
                store.rating_count = len(store_reviews)
                db.session.commit()
        
        return jsonify({
            'success': True,
            'data': review.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/reviews/<product_id>', methods=['GET'])
def get_product_reviews(product_id):
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in reviews]
    })

# ============================================
# FAVORITOS API
# ============================================

@api_bp.route('/favorites', methods=['POST'])
@csrf.exempt
@login_required
def toggle_favorite():
    try:
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
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/favorites', methods=['GET'])
@login_required
def get_favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    products = [f.product for f in favorites if f.product and f.product.is_active]
    
    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in products]
    })

# ============================================
# SEGUIDORES API
# ============================================

@api_bp.route('/followers', methods=['POST'])
@csrf.exempt
@login_required
def toggle_follower():
    try:
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
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/followers/<store_id>', methods=['GET'])
@login_required
def get_followers(store_id):
    count = Follower.query.filter_by(store_id=store_id).count()
    is_following = Follower.query.filter_by(
        user_id=current_user.id,
        store_id=store_id
    ).first() is not None
    
    return jsonify({
        'success': True,
        'count': count,
        'is_following': is_following
    })

# ============================================
# ÓRDENES API
# ============================================

@api_bp.route('/orders', methods=['POST'])
@csrf.exempt
@login_required
@customer_required
def create_order_api():
    try:
        data = request.json
        
        order_number = f"MZ-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"
        
        items = data.get('items', [])
        subtotal = sum(item['price'] * item['quantity'] for item in items)
        shipping_cost = data.get('shipping_cost', 0)
        discount = data.get('discount', 0)
        total = subtotal + shipping_cost - discount
        
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
                title='📦 Nuevo Pedido',
                message=f'Has recibido un pedido #{order_number} por Bs {total:.2f}',
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

@api_bp.route('/orders/<order_id>/cancel', methods=['POST'])
@csrf.exempt
@login_required
def cancel_order_api(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        if order.user_id != current_user.id:
            return jsonify({'error': 'No autorizado'}), 403
        
        if order.status not in ['pendiente', 'confirmado']:
            return jsonify({'error': 'No se puede cancelar este pedido'}), 400
        
        order.status = 'cancelado'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Pedido cancelado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/orders/<order_id>/status', methods=['PUT'])
@csrf.exempt
@login_required
def update_order_status_api(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        store = Store.query.filter_by(user_id=current_user.id).first()
        
        if not store or order.store_id != store.id:
            return jsonify({'error': 'No autorizado'}), 403
        
        new_status = request.json.get('status')
        
        if new_status not in ['pendiente', 'confirmado', 'enviado', 'entregado', 'cancelado']:
            return jsonify({'error': 'Estado inválido'}), 400
        
        order.status = new_status
        
        if new_status == 'entregado':
            order.delivered_at = datetime.utcnow()
        
        db.session.commit()
        
        # Notificar al cliente
        notification = Notification(
            user_id=order.user_id,
            type='order',
            title=f'Pedido #{order.order_number}',
            message=f'Tu pedido ha sido {order.get_status_label()}',
            link=f'/orders/{order.id}'
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': order.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ============================================
# NOTIFICACIONES API
# ============================================

@api_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    return jsonify({
        'success': True,
        'data': [n.to_dict() for n in notifications]
    })

@api_bp.route('/notifications/unread', methods=['GET'])
@login_required
def get_unread_notifications():
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'count': count})

@api_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@csrf.exempt
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@csrf.exempt
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    return jsonify({'success': True})

# ============================================
# ESTADÍSTICAS PARA DASHBOARD
# ============================================

@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    store = Store.query.filter_by(user_id=current_user.id).first()
    
    if not store:
        return jsonify({'success': False, 'error': 'No tienes una tienda'}), 400
    
    total_products = Product.query.filter_by(store_id=store.id).count()
    total_orders = Order.query.filter_by(store_id=store.id).count()
    pending_orders = Order.query.filter_by(store_id=store.id, status='pendiente').count()
    
    # Ventas totales
    sales = db.session.query(db.func.sum(Order.total)).filter(
        Order.store_id == store.id,
        Order.status == 'entregado'
    ).scalar() or 0
    
    # Productos con stock bajo
    low_stock = Product.query.filter(
        Product.store_id == store.id,
        Product.stock <= Product.min_stock,
        Product.stock > 0
    ).count()
    
    return jsonify({
        'success': True,
        'data': {
            'total_products': total_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_sales': float(sales),
            'low_stock': low_stock,
            'followers': store.followers_count,
            'rating': store.rating_avg
        }
    })