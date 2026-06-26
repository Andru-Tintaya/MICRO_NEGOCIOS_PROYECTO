import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image

def save_image_local(file, folder='products'):
    """Guardar imagen localmente"""
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    # Optimizar imagen
    try:
        img = Image.open(file_path)
        if img.width > 1200 or img.height > 1200:
            img.thumbnail((1200, 1200))
            img.save(file_path, optimize=True, quality=85)
    except:
        pass
    
    return f"/static/uploads/{folder}/{unique_filename}"

def delete_image_local(image_path):
    """Eliminar imagen local"""
    if image_path:
        relative_path = image_path.replace('/static/uploads/', '')
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    return False

def save_image_supabase(file, bucket, folder='products'):
    """Guardar imagen en Supabase Storage"""
    try:
        from supabase import create_client
        supabase = create_client(
            current_app.config.get('SUPABASE_URL'),
            current_app.config.get('SUPABASE_SERVICE_KEY')
        )
        
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = f"{folder}/{unique_filename}"
        
        # Subir a Supabase
        upload_result = supabase.storage.from_(bucket).upload(file_path, file.read())
        
        if upload_result:
            public_url = supabase.storage.from_(bucket).get_public_url(file_path)
            if isinstance(public_url, dict):
                return public_url.get('publicUrl')
            return str(public_url)
        
        return None
    except Exception as e:
        print(f"❌ Error subiendo a Supabase: {e}")
        return None

def save_image(file, folder='products'):
    """Guardar imagen (local o Supabase)"""
    # Determinar si usar Supabase o local
    if current_app.config.get('SUPABASE_URL'):
        return save_image_supabase(file, current_app.config.get('SUPABASE_BUCKET', 'product-images'), folder)
    else:
        return save_image_local(file, folder)

def delete_image(image_path):
    """Eliminar imagen (local o Supabase)"""
    # Por ahora solo implementamos local
    if image_path and not image_path.startswith('http'):
        return delete_image_local(image_path)
    return False