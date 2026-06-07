FROM python:3.12-slim

WORKDIR /app

# Copiar requirements y código
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el backend
COPY backend/ .

# Copiar frontend build
COPY backend/static/ /app/static/

ENV PORT=10000
ENV PYTHONPATH=/app

EXPOSE 10000
CMD ["python", "-m", "app.main"]
