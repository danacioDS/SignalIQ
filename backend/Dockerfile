FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=10000

# Usar el nuevo archivo api.py
CMD ["python", "-m", "app.api"]
