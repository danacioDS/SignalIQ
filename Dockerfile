FROM python:3.12-slim

WORKDIR /app

# Copiar requirements.txt y código
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

ENV PORT=10000
ENV PYTHONPATH=/app

EXPOSE 10000
CMD ["python", "-m", "app.main"]
