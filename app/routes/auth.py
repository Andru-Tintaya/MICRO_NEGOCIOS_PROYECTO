from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.store import Store
from app.utils.validators import validate_email, validate_whatsapp, validate_password
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from datetime import datetime, timedelta
import secrets

# Definir formularios
class LoginForm(FlaskForm):
    identifier = StringField('Email o WhatsApp', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recordarme')

class RegisterForm(FlaskForm):
    full_name = StringField('Nombre Completo', validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    whatsapp = StringField('WhatsApp', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Tipo de Cuenta', choices=[('cliente', 'Cliente'), ('vendedor', 'Vendedor')])

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            email = form.email.data
            whatsapp = form.whatsapp.data
            full_name = form.full_name.data
            password = form.password.data
            role = form.role.data
            
            # Validaciones
            if not validate_email(email):
                flash('Email inválido', 'error')
                return render_template('auth/register.html', form=form)
            
            if not validate_whatsapp(whatsapp):
                flash('WhatsApp inválido (formato: +59170000000)', 'error')
                return render_template('auth/register.html', form=form)
            
            if not validate_password(password):
                flash('La contraseña debe tener al menos 8 caracteres, una mayúscula y un número', 'error')
                return render_template('auth/register.html', form=form)
            
            # Verificar si ya existe
            if User.query.filter_by(email=email).first():
                flash('Este email ya está registrado', 'error')
                return render_template('auth/register.html', form=form)
            
            if User.query.filter_by(whatsapp=whatsapp).first():
                flash('Este WhatsApp ya está registrado', 'error')
                return render_template('auth/register.html', form=form)
            
            # Crear usuario
            user = User(
                email=email,
                whatsapp=whatsapp,
                full_name=full_name,
                password_hash=generate_password_hash(password),
                role=role,
                is_verified=True
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('¡Registro exitoso! Inicia sesión para continuar.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        identifier = form.identifier.data
        password = form.password.data
        remember = form.remember.data
        
        if not identifier or not password:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('auth/login.html', form=form)
        
        # Buscar por email o whatsapp
        user = User.query.filter(
            (User.email == identifier) | (User.whatsapp == identifier)
        ).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Tu cuenta está desactivada. Contacta al soporte.', 'error')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            session['user_id'] = user.id
            session['role'] = user.role
            session['full_name'] = user.full_name
            
            flash(f'¡Bienvenido, {user.full_name}!', 'success')
            
            # Redirigir según rol
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif user.is_vendor():
                store = Store.query.filter_by(user_id=user.id).first()
                if store:
                    return redirect(url_for('store.dashboard', store_id=store.id))
                else:
                    return redirect(url_for('store.create_store'))
            else:
                return redirect(url_for('index'))
        
        flash('Credenciales incorrectas', 'error')
    
    return render_template('auth/login.html', form=form)

# ✅ LOGOUT CORREGIDO - Redirige directamente al login
@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Cerrar sesión - Redirige al login"""
    logout_user()
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            flash('Se ha enviado un enlace de recuperación a tu email', 'success')
        else:
            flash('No se encontró una cuenta con ese email', 'error')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/profile')
@login_required
def profile():
    """Página de perfil del usuario"""
    user = User.query.get(current_user.id)
    return render_template('auth/profile.html', user=user)