FROM python:3.12-slim

WORKDIR /app

# Copiar requirements y instalar dependencias
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend
COPY backend/ .

# Variables de entorno
ENV PORT=10000
ENV PYTHONUNBUFFERED=1

EXPOSE 10000

# Comando para iniciar la aplicación
CMD ["python", "-m", "app.main"]
