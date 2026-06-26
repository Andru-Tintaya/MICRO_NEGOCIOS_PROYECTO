from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.category import Category
from app.utils.decorators import admin_required
from app.utils.helpers import slugify
import uuid

category_bp = Blueprint('category', __name__, url_prefix='/categories')

@category_bp.route('/')
def list():
    categories = Category.query.filter_by(parent_id=None).all()
    return render_template('category/list.html', categories=categories)

@category_bp.route('/<slug>')
def view(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    products = category.products
    return render_template('category/view.html', category=category, products=products)

@category_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon')
        parent_id = request.form.get('parent_id')
        
        if not name:
            flash('El nombre es obligatorio', 'error')
            return render_template('category/create.html', categories=Category.query.all())
        
        category = Category(
            name=name,
            slug=slugify(name),
            description=description,
            icon=icon,
            parent_id=parent_id if parent_id else None
        )
        
        db.session.add(category)
        db.session.commit()
        flash('Categoría creada exitosamente', 'success')
        return redirect(url_for('category.list'))
    
    categories = Category.query.all()
    return render_template('category/create.html', categories=categories)

@category_bp.route('/edit/<category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(category_id):
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name', category.name)
        category.description = request.form.get('description', category.description)
        category.icon = request.form.get('icon', category.icon)
        category.parent_id = request.form.get('parent_id') or None
        
        db.session.commit()
        flash('Categoría actualizada', 'success')
        return redirect(url_for('category.list'))
    
    categories = Category.query.filter(Category.id != category_id).all()
    return render_template('category/edit.html', category=category, categories=categories)

@category_bp.route('/delete/<category_id>', methods=['POST'])
@login_required
@admin_required
def delete(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Categoría eliminada', 'success')
    return redirect(url_for('category.list'))