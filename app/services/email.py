from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail
import os

def send_email(subject, recipients, template, **kwargs):
    """Enviar email usando Flask-Mail"""
    if not current_app.config.get('MAIL_USERNAME'):
        print("⚠️ Email no configurado")
        return
    
    try:
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            html=render_template(template, **kwargs),
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        print(f"✅ Email enviado a {recipients}")
    except Exception as e:
        print(f"❌ Error enviando email: {e}")

def send_welcome_email(user):
    """Enviar email de bienvenida"""
    send_email(
        subject='🎉 Bienvenido a MiZona',
        recipients=user.email,
        template='email/welcome.html',
        user=user
    )

def send_order_notification(user, order):
    """Enviar notificación de pedido"""
    send_email(
        subject=f'📦 Nuevo Pedido #{order.order_number}',
        recipients=user.email,
        template='email/order_notification.html',
        user=user,
        order=order
    )

def send_password_reset(user, token):
    """Enviar email de recuperación de contraseña"""
    reset_link = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/auth/reset-password/{token}"
    send_email(
        subject='🔑 Recuperación de Contraseña - MiZona',
        recipients=user.email,
        template='email/reset_password.html',
        user=user,
        reset_link=reset_link
    )