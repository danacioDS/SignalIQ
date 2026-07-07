FROM python:3.11-slim

WORKDIR /app

# Copiar requirements.txt
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY backend/app/ ./app/

# Puerto para Render
ENV PORT=10000

# Comando de inicio
CMD ["python", "-m", "app.main"]
