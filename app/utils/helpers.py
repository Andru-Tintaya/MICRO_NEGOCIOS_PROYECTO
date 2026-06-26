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

def save_image(file, folder='products'):
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
    
    # 🔥 CAMBIO IMPORTANTE: Devolver la URL completa para static
    return f"/static/uploads/{folder}/{filename}"

def delete_image(filepath):
    if not filepath:
        return False
    full_path = os.path.join(current_app.root_path, 'static', filepath)
    if os.path.exists(full_path):
        os.remove(full_path)
        return True
    return False