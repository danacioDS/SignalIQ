FROM python:3.12-slim

WORKDIR /app

# Copiar requirements.txt del backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del backend
COPY backend/ .

# Variables de entorno
ENV PORT=10000
EXPOSE 10000

# Comando para ejecutar la aplicación
CMD ["python", "-m", "app.main"]
