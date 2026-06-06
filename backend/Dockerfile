FROM python:3.12-slim

WORKDIR /app

# Copiar requirements.txt desde la ubicación correcta
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY app/ ./app/

ENV PORT=5000
EXPOSE 5000

CMD ["python", "-m", "app.main"]
