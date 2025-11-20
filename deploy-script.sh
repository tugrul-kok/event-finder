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
cp scraper.py $PROJECT_DIR/
cp requirements.txt $PROJECT_DIR/
cp .env $PROJECT_DIR/

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
cp events.service /etc/systemd/system/
systemctl daemon-reload

# 9. Nginx konfigürasyonu
echo -e "${YELLOW}🌐 Nginx ayarlanıyor...${NC}"
cp nginx.conf /etc/nginx/sites-available/events
ln -sf /etc/nginx/sites-available/events /etc/nginx/sites-enabled/
nginx -t

# 10. İzinleri ayarla
echo -e "${YELLOW}🔐 Dosya izinleri ayarlanıyor...${NC}"
chown -R www-data:www-data $PROJECT_DIR
chown -R www-data:www-data /var/log/events
chmod -R 755 $PROJECT_DIR

# 11. Cron job'u kur
echo -e "${YELLOW}🕐 Cron job kuruluyor...${NC}"
chmod +x setup_cron.sh
./setup_cron.sh

# 12. Servisleri başlat
echo -e "${YELLOW}🚀 Servisler başlatılıyor...${NC}"
systemctl restart $SERVICE_NAME
systemctl enable $SERVICE_NAME
systemctl restart nginx

# 13. Örnek verilerle veritabanını doldur (ilk kurulum için)
echo -e "${YELLOW}🌱 Veritabanı örnek verilerle dolduruluyor...${NC}"
sleep 3
curl -X POST http://localhost:5000/api/seed || echo "Seed endpoint'e ulaşılamadı (normal olabilir)"

# 14. İlk scraping'i çalıştır
echo -e "${YELLOW}🔍 İlk scraping başlatılıyor...${NC}"
sudo -u www-data $PROJECT_DIR/run_scraper.sh &

# 15. Durum kontrolü
echo -e "${YELLOW}✅ Durum kontrol ediliyor...${NC}"
sleep 2
systemctl status $SERVICE_NAME --no-pager
curl http://localhost:5000/health

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
echo "  • API: http://your-domain.com/api"
echo "  • Health: http://your-domain.com/health"
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