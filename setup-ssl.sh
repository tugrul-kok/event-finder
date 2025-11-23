#!/bin/bash

# SSL/HTTPS Nginx Yapılandırma Script'i
# Mevcut SSL sertifikasını kullanarak Nginx'i HTTPS için yapılandırır
# Bu script'i root veya sudo ile çalıştırın

# set -e yerine kontrollü hata yönetimi kullanıyoruz
set +e

echo "🔒 SSL/HTTPS Nginx Yapılandırması Başlıyor..."

# Renkli çıktı için
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DOMAIN="events.tugrul.app"

# Environment variable'lardan SSL dosya yollarını al (varsa)
if [ -n "$SSL_CERT" ] && [ -n "$SSL_KEY" ]; then
    echo -e "${BLUE}📋 Environment variable'lardan SSL dosya yolları alındı${NC}"
else
    # 1. Mevcut SSL sertifikasını bul
    echo -e "${YELLOW}🔍 Mevcut SSL sertifikası aranıyor...${NC}"
    
    # Olası sertifika konumları
CERT_PATHS=(
    "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
    "/etc/letsencrypt/live/${DOMAIN}/cert.pem"
    "/etc/ssl/certs/${DOMAIN}.crt"
    "/etc/nginx/ssl/${DOMAIN}.crt"
    "/etc/ssl/${DOMAIN}/fullchain.pem"
)

SSL_CERT=""
SSL_KEY=""

for cert_path in "${CERT_PATHS[@]}"; do
    if [ -f "$cert_path" ]; then
        SSL_CERT="$cert_path"
        echo -e "${GREEN}✅ SSL sertifikası bulundu: $cert_path${NC}"
        
        # Key dosyasını bul
        if [[ "$cert_path" == *"letsencrypt"* ]]; then
            KEY_PATH="${cert_path%/*}/privkey.pem"
            if [ -f "$KEY_PATH" ]; then
                SSL_KEY="$KEY_PATH"
                echo -e "${GREEN}✅ SSL key bulundu: $KEY_PATH${NC}"
                break
            fi
        elif [[ "$cert_path" == *".crt" ]]; then
            KEY_PATH="${cert_path%.crt}.key"
            if [ -f "$KEY_PATH" ]; then
                SSL_KEY="$KEY_PATH"
                echo -e "${GREEN}✅ SSL key bulundu: $KEY_PATH${NC}"
                break
            fi
        fi
    fi
done

# Eğer sertifika bulunamadıysa, mevcut nginx config'inden kontrol et
if [ -z "$SSL_CERT" ]; then
    echo -e "${YELLOW}🔍 Nginx config dosyalarında SSL sertifikası aranıyor...${NC}"
    EXISTING_CERT=$(grep -r "ssl_certificate" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null | grep -v "#" | head -1 | awk '{print $2}' | tr -d ';' || true)
    
    if [ -n "$EXISTING_CERT" ] && [ -f "$EXISTING_CERT" ]; then
        SSL_CERT="$EXISTING_CERT"
        echo -e "${GREEN}✅ Mevcut Nginx config'inden SSL sertifikası bulundu: $SSL_CERT${NC}"
        
        # Key dosyasını bul
        EXISTING_KEY=$(grep -r "ssl_certificate_key" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null | grep -v "#" | head -1 | awk '{print $2}' | tr -d ';' || true)
        if [ -n "$EXISTING_KEY" ] && [ -f "$EXISTING_KEY" ]; then
            SSL_KEY="$EXISTING_KEY"
            echo -e "${GREEN}✅ Mevcut Nginx config'inden SSL key bulundu: $SSL_KEY${NC}"
        fi
    fi
fi

fi  # Environment variable kontrolünün kapanışı

# Hala bulunamadıysa hata ver
if [ -z "$SSL_CERT" ] || [ -z "$SSL_KEY" ]; then
    echo -e "${RED}❌ SSL sertifikası bulunamadı!${NC}"
    echo ""
    echo "Mevcut SSL sertifikalarını kontrol edin:"
    echo "  ls -la /etc/letsencrypt/live/"
    echo "  ls -la /etc/ssl/"
    echo "  grep -r ssl_certificate /etc/nginx/"
    echo ""
    echo "Eğer SSL sertifikası farklı bir konumdaysa, script'i şu şekilde çalıştırın:"
    echo "  SSL_CERT=/path/to/cert.pem SSL_KEY=/path/to/key.pem bash setup-ssl.sh"
    echo ""
    echo "Veya manuel olarak nginx config'ini güncelleyin."
    exit 1
fi

# SSL dosyalarının varlığını kontrol et
if [ ! -f "$SSL_CERT" ]; then
    echo -e "${RED}❌ SSL sertifika dosyası bulunamadı: $SSL_CERT${NC}"
    exit 1
fi

if [ ! -f "$SSL_KEY" ]; then
    echo -e "${RED}❌ SSL key dosyası bulunamadı: $SSL_KEY${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Kullanılacak SSL dosyaları:${NC}"
echo "  Certificate: $SSL_CERT"
echo "  Key: $SSL_KEY"

# 2. Nginx config'ini HTTPS için güncelle
echo -e "${YELLOW}🌐 Nginx yapılandırması güncelleniyor...${NC}"

# Heredoc delimiter'ını tırnaklı yaparak nginx değişkenlerinin shell tarafından expand edilmesini engelle
# SSL sertifika yollarını sonra sed ile replace edeceğiz
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
    
    # SSL sertifikaları (mevcut sertifika kullanılıyor)
    ssl_certificate SSL_CERT_PLACEHOLDER;
    ssl_certificate_key SSL_KEY_PLACEHOLDER;
    
    # SSL yapılandırması (güvenlik için)
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

# 3. Nginx config'i test et
echo -e "${YELLOW}✅ Nginx yapılandırması test ediliyor...${NC}"
if ! nginx -t; then
    echo -e "${RED}❌ Nginx config test başarısız!${NC}"
    echo -e "${YELLOW}📋 Config dosyasını kontrol edin:${NC}"
    echo "  cat /etc/nginx/sites-available/events"
    echo ""
    echo -e "${YELLOW}📋 Detaylı hata mesajı:${NC}"
    nginx -t 2>&1
    exit 1
fi

# 4. Nginx'i yeniden başlat
echo -e "${YELLOW}🚀 Nginx yeniden başlatılıyor...${NC}"
if systemctl is-active --quiet nginx; then
    echo "Nginx çalışıyor, reload ediliyor..."
    if ! systemctl reload nginx; then
        echo -e "${YELLOW}⚠️  Reload başarısız, restart deneniyor...${NC}"
        systemctl restart nginx
    fi
else
    echo "Nginx çalışmıyor, başlatılıyor..."
    systemctl start nginx
fi

# Nginx durumunu kontrol et
sleep 2
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx başarıyla başlatıldı${NC}"
else
    echo -e "${RED}❌ Nginx başlatılamadı!${NC}"
    echo -e "${YELLOW}📋 Durum kontrolü:${NC}"
    systemctl status nginx --no-pager
    echo -e "${YELLOW}📋 Loglar:${NC}"
    journalctl -u nginx --no-pager -n 20
    exit 1
fi

# 5. Test
echo -e "${YELLOW}🧪 SSL yapılandırması test ediliyor...${NC}"
sleep 3
if curl -f -I https://$DOMAIN/health 2>/dev/null; then
    echo -e "${GREEN}✅ HTTPS health check başarılı${NC}"
else
    echo -e "${YELLOW}⚠️  HTTPS health check başarısız (servis henüz hazır olmayabilir)${NC}"
    echo -e "${YELLOW}💡 HTTP üzerinden test ediliyor...${NC}"
    curl -f -I http://$DOMAIN/health 2>/dev/null && echo -e "${YELLOW}⚠️  HTTP çalışıyor ama HTTPS çalışmıyor${NC}" || echo -e "${YELLOW}⚠️  Her iki protokol de henüz hazır değil${NC}"
fi

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ SSL/HTTPS kurulumu tamamlandı!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}🔗 URL'ler:${NC}"
echo "  • HTTPS: https://events.tugrul.app"
echo "  • API: https://events.tugrul.app/api"
echo "  • Health: https://events.tugrul.app/health"
echo ""
echo -e "${YELLOW}📝 Notlar:${NC}"
echo "  • Mevcut SSL sertifikası kullanılıyor: $SSL_CERT"
echo "  • HTTP trafiği otomatik olarak HTTPS'e yönlendiriliyor"
if [[ "$SSL_CERT" == *"letsencrypt"* ]]; then
    echo "  • Let's Encrypt sertifikası otomatik olarak yenilenecek (certbot timer aktifse)"
    echo "  • Sertifika durumunu kontrol etmek için: certbot certificates"
fi
echo ""

