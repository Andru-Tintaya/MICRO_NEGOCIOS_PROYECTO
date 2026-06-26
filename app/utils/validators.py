import re

def validate_email(email):
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_whatsapp(whatsapp):
    """Validar formato de WhatsApp (+59170000000)"""
    pattern = r'^\+\d{1,3}\d{8,10}$'
    return re.match(pattern, whatsapp) is not None

def validate_password(password):
    """Validar contraseña: mínimo 8 caracteres, mayúscula, número"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    return True

def validate_phone(phone):
    """Validar número de teléfono (solo números)"""
    return re.match(r'^\d{7,10}$', phone) is not None

def validate_url(url):
    """Validar URL"""
    pattern = r'^https?:\/\/[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None