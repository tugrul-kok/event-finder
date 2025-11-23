FROM python:3.10-slim

WORKDIR /app

# Gerekli sistem paketleri
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılıkları yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Model önbelleği için klasör
RUN mkdir -p /app/model_cache
ENV HF_HOME=/app/model_cache

# Dosyaları kopyala
COPY . .

# Ortam değişkenleri
ENV FLASK_APP=events_backend.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5001

CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5001", "--timeout", "120", "events_backend:app"]