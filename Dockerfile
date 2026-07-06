FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt desde backend/
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación desde backend/app/
COPY backend/app/ ./app/

# Puerto
EXPOSE 10000

# Comando para ejecutar
CMD ["python", "-m", "app.main"]
# FORCE CORS FIX Mon Jul  6 17:22:44 -04 2026
