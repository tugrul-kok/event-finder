FROM python:3.10-slim

# Çalışma dizinini ayarla
WORKDIR /app

# 1. Gerekli sistem paketlerini yükle (C/C++ derleyicileri, XML kütüphaneleri)
# Bu, lxml, numpy ve sentence-transformers gibi paketlerin kurulması için zorunludur.
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. PyTorch'un CPU versiyonunu önceden yükle (Sentense Transformers için)
# Bu, büyük GPU bağımlılıklarının indirilmesini engeller.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 3. Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Model önbelleği için klasör ve ENV ayarı
RUN mkdir -p /app/model_cache
ENV HF_HOME=/app/model_cache

# Tüm proje dosyalarını kopyala
COPY . .

# Ortam değişkenleri
ENV FLASK_APP=events_backend.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# PyTorch bellek optimizasyonu (RAM tasarrufu için kritik)
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1

EXPOSE 5001

# SON SATIR: Worker sayısını 1, Thread sayısını 4 olarak ayarla (RAM Tasarrufu için kritik)
CMD ["gunicorn", "--workers", "1", "--threads", "4", "--bind", "0.0.0.0:5001", "events_backend:app"]