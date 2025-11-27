FROM python:3.10-slim

# Çalışma dizinini ayarla
WORKDIR /app

# 1. Gerekli sistem paketlerini yükle (C/C++ derleyicileri, XML kütüphaneleri, Chrome için)
# Bu, lxml, numpy, sentence-transformers ve Selenium için gerekli
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    curl \
    wget \
    gnupg \
    ca-certificates \
    unzip \
    # Chrome ve ChromeDriver için gerekli paketler
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 2. PyTorch'un CPU versiyonunu önceden yükle (Sentense Transformers için)
# Bu, büyük GPU bağımlılıklarının indirilmesini engeller.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 3. Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Chrome ve ChromeDriver kurulumu (Selenium için - opsiyonel, Biletix scraping için)
# Not: Eğer Selenium kullanılmayacaksa bu adımı atlayabilirsiniz
# Modern yöntem: apt-key deprecated, gpg keyring kullanılıyor
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

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