FROM python:3.12-slim

WORKDIR /app

# Copiar requirements.txt y instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO el contenido de la carpeta app/
COPY app/ ./app/

# Establecer el puerto para Render
ENV PORT=10000
EXPOSE 10000

# Comando para ejecutar la aplicación
CMD ["python", "-m", "app.main"]
