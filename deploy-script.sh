#!/bin/bash

# Events Backend Deployment Script (Güncellenmiş - Scraper ile)
# Bu script'i root veya sudo ile çalıştırın

set -e

echo "🚀 Events Backend + Scraper Deployment Başlıyor..."

# Renkli çıktı için
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Değişkenler
PROJECT_DIR="/var/www/events"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="events"

# 1. Sistem güncellemesi
echo -e "${YELLOW}📦 Sistem paketleri güncelleniyor...${NC}"
apt-get update
apt-get upgrade -y

# 2. Gerekli paketleri yükle
echo -e "${YELLOW}📦 Gerekli paketler yükleniyor...${NC}"
apt-get install -y python3 python3-pip python3-venv nginx mongodb cron

# 3. MongoDB'yi başlat
echo -e "${YELLOW}🗄️  MongoDB başlatılıyor...${NC}"
systemctl start mongodb
systemctl enable mongodb

# 4. Proje dizinini oluştur
echo -e "${YELLOW}📁 Proje dizini oluşturuluyor...${NC}"
mkdir -p $PROJECT_DIR
mkdir -p /var/log/events

# 5. Dosyaları kopyala
echo -e "${YELLOW}📋 Dosyalar kopyalanıyor...${NC}"
cp events_backend.py $PROJECT_DIR/app.py
cp scraper-script.py $PROJECT_DIR/scraper-script.py
cp rag_engine.py $PROJECT_DIR/
cp rag_retriever.py $PROJECT_DIR/
cp requirements.txt $PROJECT_DIR/
cp .env $PROJECT_DIR/ 2>/dev/null || echo "⚠️  .env dosyası bulunamadı, manuel oluşturmanız gerekecek"

# Web interface dosyalarını kopyala
mkdir -p $PROJECT_DIR/web
cp -r web/* $PROJECT_DIR/web/ 2>/dev/null || echo "⚠️  Web dosyaları bulunamadı"

# 6. Virtual environment oluştur
echo -e "${YELLOW}🐍 Python virtual environment oluşturuluyor...${NC}"
cd $PROJECT_DIR
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# 7. Python paketlerini yükle
echo -e "${YELLOW}📦 Python paketleri yükleniyor (scraper + AI dahil)...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 8. Systemd service dosyasını kopyala
echo -e "${YELLOW}⚙️  Systemd service ayarlanıyor...${NC}"
cp systemd-service.txt /etc/systemd/system/events.service
systemctl daemon-reload

# 9. Nginx konfigürasyonu
echo -e "${YELLOW}🌐 Nginx ayarlanıyor...${NC}"

# Mevcut SSL sertifikasını kontrol et
SSL_CERT=""
SSL_KEY=""

# Let's Encrypt sertifikasını kontrol et
if [ -f "/etc/letsencrypt/live/events.tugrul.app/fullchain.pem" ]; then
    SSL_CERT="/etc/letsencrypt/live/events.tugrul.app/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/events.tugrul.app/privkey.pem"
    echo -e "${GREEN}✅ Mevcut SSL sertifikası bulundu, HTTPS yapılandırması yapılıyor...${NC}"
fi

# Nginx config'i oluştur
if [ -n "$SSL_CERT" ] && [ -f "$SSL_CERT" ]; then
    # HTTPS yapılandırması
    cat > /etc/nginx/sites-available/events << 'NGINX_EOF'
# HTTP'den HTTPS'e yönlendirme
server {
    listen 80;
    server_name events.tugrul.app 65.21.182.26;
    
    # Let's Encrypt doğrulama için
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Tüm HTTP trafiğini HTTPS'e yönlendir
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name events.tugrul.app 65.21.182.26;
    
    # SSL sertifikaları
    ssl_certificate SSL_CERT_PLACEHOLDER;
    ssl_certificate_key SSL_KEY_PLACEHOLDER;
    
    # SSL yapılandırması
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    client_max_body_size 10M;
    
    # Web interface (root)
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API endpoints
    location /api {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Rate limiting (DDoS koruması)
    # Not: limit_req_zone http bloğunda tanımlanmalı
    # Eğer nginx.conf'da limit_req_zone tanımlı değilse aşağıdaki satırı yorum satırı yapın
    # limit_req zone=api_limit burst=20 nodelay;
    
    # Logs
    access_log /var/log/nginx/events_access.log;
    error_log /var/log/nginx/events_error.log;
}
NGINX_EOF

    # SSL sertifika yollarını replace et
    sed -i "s|SSL_CERT_PLACEHOLDER|$SSL_CERT|g" /etc/nginx/sites-available/events
    sed -i "s|SSL_KEY_PLACEHOLDER|$SSL_KEY|g" /etc/nginx/sites-available/events
else
    # Sadece HTTP yapılandırması (SSL yoksa)
    echo -e "${YELLOW}⚠️  SSL sertifikası bulunamadı, sadece HTTP yapılandırması yapılıyor...${NC}"
    cat > /etc/nginx/sites-available/events << 'NGINX_EOF'
server {
    listen 80;
    server_name events.tugrul.app 65.21.182.26;
    
    client_max_body_size 10M;
    
    # Web interface (root)
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API endpoints
    location /api {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Rate limiting (DDoS koruması)
    # Not: limit_req_zone http bloğunda tanımlanmalı
    # Eğer nginx.conf'da limit_req_zone tanımlı değilse aşağıdaki satırı yorum satırı yapın
    # limit_req zone=api_limit burst=20 nodelay;
    
    # Logs
    access_log /var/log/nginx/events_access.log;
    error_log /var/log/nginx/events_error.log;
}
NGINX_EOF
fi

ln -sf /etc/nginx/sites-available/events /etc/nginx/sites-enabled/
nginx -t

# 10. İzinleri ayarla
echo -e "${YELLOW}🔐 Dosya izinleri ayarlanıyor...${NC}"
chown -R www-data:www-data $PROJECT_DIR
chown -R www-data:www-data /var/log/events
chmod -R 755 $PROJECT_DIR

# 11. Cron job'u kur
echo -e "${YELLOW}🕐 Cron job kuruluyor...${NC}"
chmod +x cron-setup.sh
cp cron-setup.sh $PROJECT_DIR/
cd $PROJECT_DIR
./cron-setup.sh
cd -

# 12. Servisleri başlat
echo -e "${YELLOW}🚀 Servisler başlatılıyor...${NC}"
systemctl restart $SERVICE_NAME
systemctl enable $SERVICE_NAME
systemctl restart nginx

# 13. İlk scraping'i çalıştır (veritabanını doldur)
echo -e "${YELLOW}🔍 İlk scraping başlatılıyor (veritabanını dolduracak)...${NC}"
sleep 3
sudo -u www-data $PROJECT_DIR/run_scraper.sh &

# 15. Durum kontrolü
echo -e "${YELLOW}✅ Durum kontrol ediliyor...${NC}"
sleep 2
systemctl status $SERVICE_NAME --no-pager
curl http://localhost:5001/health

echo -e "${GREEN}✅ Deployment tamamlandı!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Events sistemi başarıyla kuruldu!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📝 ÖNEMLİ: Token'ları eklemeyi unutmayın!${NC}"
echo "1. Telegram Bot Token: nano /var/www/events/.env"
echo "2. Gemini API Key: nano /var/www/events/.env"
echo ""
echo -e "${GREEN}🔗 URL'ler:${NC}"
if [ -n "$SSL_CERT" ] && [ -f "$SSL_CERT" ]; then
    echo "  • Web Interface: https://events.tugrul.app"
    echo "  • API: https://events.tugrul.app/api"
    echo "  • Health: https://events.tugrul.app/health"
else
    echo "  • Web Interface: http://events.tugrul.app"
    echo "  • API: http://events.tugrul.app/api"
    echo "  • Health: http://events.tugrul.app/health"
    echo -e "${YELLOW}  💡 HTTPS için: sudo bash setup-ssl.sh${NC}"
fi
echo ""
echo -e "${GREEN}🤖 Telegram Bot:${NC}"
echo "  • Botunuzu Telegram'da bulun ve /start yazın"
echo ""
echo -e "${GREEN}🕐 Scraper:${NC}"
echo "  • Otomatik: Her gece saat 02:00"
echo "  • Manuel: sudo -u www-data /var/www/events/run_scraper.sh"
echo ""
echo -e "${YELLOW}📋 Yararlı Komutlar:${NC}"
echo "  • Servisi yeniden başlat: sudo systemctl restart $SERVICE_NAME"
echo "  • API logları: sudo journalctl -u $SERVICE_NAME -f"
echo "  • Scraper logları: sudo tail -f /var/log/events/scraper.log"
echo "  • Cron logları: sudo tail -f /var/log/events/scraper_cron.log"
echo "  • Veritabanı: mongo events_db"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"