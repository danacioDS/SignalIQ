FROM python:3.12-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements primero (para cache)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY backend/ .

# Crear __init__.py si no existe
RUN touch app/__init__.py

# Exponer puerto
EXPOSE 10000

# Comando para correr la API
# Usamos python -m app.main para que funcione el import relativo
CMD ["python", "-m", "app.main"]
