FROM python:3.11-slim

WORKDIR /app

# Copiar requirements.txt desde la raíz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend
COPY backend/app/ ./app/

# Puerto para Render
ENV PORT=10000

# Comando de inicio
CMD ["python", "-m", "app.main"]
