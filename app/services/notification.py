from app.extensions import db, mail
from flask_mail import Message
from flask import current_app, render_template
from app.models.notification import Notification
from app.models.user import User
import os

def send_order_notification(user_id, order):
    """Enviar notificación de nuevo pedido"""
    user = User.query.get(user_id)
    if not user:
        return
    
    # Notificación en la app
    notification = Notification(
        user_id=user_id,
        type='order',
        title=f'📦 Nuevo Pedido #{order.order_number}',
        message=f'Has recibido un pedido por Bs {order.total:.2f}',
        link=f'/orders/{order.id}'
    )
    db.session.add(notification)
    db.session.commit()
    
    # Enviar email
    try:
        send_email(
            subject=f'Nuevo Pedido #{order.order_number} - MiZona',
            recipients=[user.email],
            template='email/order_notification.html',
            order=order,
            user=user
        )
    except Exception as e:
        print(f"Error al enviar email: {e}")

def send_welcome_email(user):
    """Enviar email de bienvenida"""
    try:
        send_email(
            subject='Bienvenido a MiZona 🎉',
            recipients=[user.email],
            template='email/welcome.html',
            user=user
        )
    except Exception as e:
        print(f"Error al enviar email de bienvenida: {e}")

def send_password_reset_email(user, token):
    """Enviar email de recuperación de contraseña"""
    try:
        reset_link = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/auth/reset-password/{token}"
        send_email(
            subject='Recuperación de Contraseña - MiZona',
            recipients=[user.email],
            template='email/reset_password.html',
            user=user,
            reset_link=reset_link
        )
    except Exception as e:
        print(f"Error al enviar email de recuperación: {e}")

def send_email(subject, recipients, template, **kwargs):
    """Enviar email usando Flask-Mail"""
    if not current_app.config.get('MAIL_USERNAME'):
        return
    
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=render_template(template, **kwargs),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")