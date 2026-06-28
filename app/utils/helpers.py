import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image

def slugify(text):
    import re
    import unicodedata
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text

def validate_image_extension(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================
# GUARDAR IMAGEN LOCAL (fallback)
# ============================================

def save_image_local(file, folder='products'):
    """Guardar imagen localmente (solo como respaldo)"""
    if not file or not file.filename:
        return None
    
    if not validate_image_extension(file.filename):
        raise ValueError("Tipo de archivo no permitido. Solo: png, jpg, jpeg, gif, webp")
    
    original_filename = secure_filename(file.filename)
    unique_id = uuid.uuid4().hex[:12]
    extension = original_filename.rsplit('.', 1)[1].lower()
    filename = f"{unique_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}"
    
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', folder)
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    try:
        with Image.open(file_path) as img:
            if max(img.size) > 1200:
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                img.save(file_path, optimize=True, quality=85)
    except Exception:
        pass
    
    return f"/static/uploads/{folder}/{filename}"

# ============================================
# ✅ GUARDAR IMAGEN EN SUPABASE (CORRECTO)
# ============================================

def save_image_supabase(file, bucket, folder='products'):
    """✅ Guardar imagen en Supabase Storage con URL correcta"""
    try:
        from supabase import create_client
        
        supabase_url = current_app.config.get('SUPABASE_URL')
        supabase_key = current_app.config.get('SUPABASE_SERVICE_KEY')
        
        if not supabase_url:
            print("❌ SUPABASE_URL no configurado")
            return save_image_local(file, folder)
        
        if not validate_image_extension(file.filename):
            raise ValueError("Tipo de archivo no permitido. Solo: png, jpg, jpeg, gif, webp")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Generar nombre único
        original_filename = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex[:12]
        extension = original_filename.rsplit('.', 1)[1].lower()
        filename = f"{unique_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}"
        file_path = f"{folder}/{filename}"
        
        # ✅ Subir a Supabase
        file.seek(0)
        upload_result = supabase.storage.from_(bucket).upload(file_path, file.read())
        
        if not upload_result:
            print("❌ Error al subir a Supabase")
            return save_image_local(file, folder)
        
        # ✅ ✅ ✅ GENERAR URL COMPLETA MANUALMENTE
        public_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{file_path}"
        
        print(f"✅ Imagen subida correctamente: {public_url}")
        return public_url
        
    except Exception as e:
        print(f"❌ Error subiendo a Supabase: {e}")
        return save_image_local(file, folder)

# ============================================
# ✅ FUNCIÓN PRINCIPAL (usa Supabase si está configurado)
# ============================================

def save_image(file, folder='products'):
    """✅ Guardar imagen: usa Supabase si está configurado"""
    if not file or not file.filename:
        return None
    
    # Si SUPABASE_URL está configurado, usar Supabase
    if current_app.config.get('SUPABASE_URL'):
        bucket = current_app.config.get('SUPABASE_BUCKET', 'product-images')
        return save_image_supabase(file, bucket, folder)
    else:
        # Fallback a local
        return save_image_local(file, folder)

# ============================================
# ELIMINAR IMAGEN
# ============================================

def delete_image(filepath):
    """Eliminar imagen (local o Supabase)"""
    if not filepath:
        return False
    
    # Si es URL de Supabase
    if filepath.startswith('http'):
        # Las imágenes en Supabase se eliminan desde el dashboard
        print("ℹ️ Las imágenes en Supabase se eliminan desde el dashboard o con la API")
        return True
    
    # Eliminar local
    if filepath.startswith('/static/'):
        filepath = filepath.replace('/static/', '', 1)
    
    full_path = os.path.join(current_app.root_path, 'static', filepath)
    if os.path.exists(full_path):
        os.remove(full_path)
        return True
    return False

# ============================================
# ✅ OBTENER URL PÚBLICA
# ============================================

def get_public_url(image_path):
    """✅ Genera la URL pública correcta (para usar en templates)"""
    if not image_path:
        return None
    
    # Si ya es URL completa, devolverla
    if image_path.startswith('http'):
        return image_path
    
    # Si es ruta local, intentar convertir a Supabase
    if '/static/uploads/' in image_path:
        clean_path = image_path.replace('/static/uploads/', '').replace('static/uploads/', '')
        clean_path = clean_path.strip('/')
        
        supabase_url = current_app.config.get('SUPABASE_URL')
        bucket = current_app.config.get('SUPABASE_BUCKET', 'product-images')
        
        if supabase_url:
            return f"{supabase_url}/storage/v1/object/public/{bucket}/{clean_path}"
    
    return image_path