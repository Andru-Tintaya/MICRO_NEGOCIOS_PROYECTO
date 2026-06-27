# Usar Python 3.12 oficial
FROM python:3.12-slim

# Instalar dependencias del sistema para Pillow y psycopg2
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero (para cachear)
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Puerto que usará Render
EXPOSE 10000

# Comando para iniciar la aplicación
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:10000"]