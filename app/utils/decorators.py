from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user
from app.models.store import Store

def admin_required(f):
    """Verifica que el usuario sea administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def vendor_required(f):
    """Verifica que el usuario sea vendedor y tenga tienda"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role != 'vendedor' and current_user.role != 'admin':
            flash('Necesitas ser vendedor para acceder.', 'warning')
            return redirect(url_for('index'))
        
        # Verificar que tenga tienda
        store = Store.query.filter_by(user_id=current_user.id).first()
        if not store and current_user.role != 'admin':
            flash('Primero debes crear tu tienda.', 'warning')
            # <--- CAMBIO IMPORTANTE AQUÍ
            return redirect(url_for('store.create_store'))  # Antes era 'store.create'
        
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    """Verifica que el usuario sea cliente (o no requiere tienda)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def store_owner_required(f):
    """Verifica que el usuario sea dueño de la tienda"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión.', 'warning')
            return redirect(url_for('auth.login'))
        
        store_id = kwargs.get('store_id')
        if not store_id:
            flash('Tienda no especificada.', 'danger')
            return redirect(url_for('store.dashboard'))
        
        store = Store.query.get(store_id)
        if not store:
            abort(404)
        
        if store.user_id != current_user.id and current_user.role != 'admin':
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function