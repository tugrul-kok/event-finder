#!/bin/bash

# Cron job kurulum scripti
# Her gece saat 02:00'de scraper çalıştırır

set -e

echo "🕐 Cron job kuruluyor..."

# Log dizini oluştur
sudo mkdir -p /var/log/events
sudo chown -R www-data:www-data /var/log/events

# Cron job için script oluştur
cat > /var/www/events/run_scraper.sh << 'EOF'
#!/bin/bash

# Events Scraper çalıştırma scripti
cd /var/www/events
source venv/bin/activate

# Scraper'ı çalıştır ve logla
python3 scraper.py >> /var/log/events/scraper_cron.log 2>&1

# Başarılı olursa timestamp yaz
if [ $? -eq 0 ]; then
    echo "✅ Scraper başarıyla tamamlandı: $(date)" >> /var/log/events/scraper_cron.log
else
    echo "❌ Scraper hatası: $(date)" >> /var/log/events/scraper_cron.log
fi
EOF

# Script'e çalıştırma izni ver
chmod +x /var/www/events/run_scraper.sh
chown www-data:www-data /var/www/events/run_scraper.sh

# Crontab'a ekle (www-data kullanıcısı için)
echo "📋 Crontab'a ekleniyor..."

# Mevcut crontab'ı yedekle
crontab -u www-data -l > /tmp/crontab.bak 2>/dev/null || true

# Yeni cron job'u ekle (eğer yoksa)
if ! crontab -u www-data -l 2>/dev/null | grep -q "run_scraper.sh"; then
    (crontab -u www-data -l 2>/dev/null; echo "# Events Scraper - Her gece saat 02:00") | crontab -u www-data -
    (crontab -u www-data -l 2>/dev/null; echo "0 2 * * * /var/www/events/run_scraper.sh") | crontab -u www-data -
    echo "✅ Cron job eklendi: Her gece saat 02:00"
else
    echo "ℹ️  Cron job zaten mevcut"
fi

# Crontab'ı göster
echo ""
echo "📅 Aktif cron jobs (www-data kullanıcısı):"
crontab -u www-data -l

# Manuel test için bilgi
echo ""
echo "=" * 50
echo "✅ Cron job kurulumu tamamlandı!"
echo ""
echo "📝 Faydalı komutlar:"
echo ""
echo "  # Scraper'ı manuel çalıştır (test):"
echo "  sudo -u www-data /var/www/events/run_scraper.sh"
echo ""
echo "  # Cron loglarını görüntüle:"
echo "  tail -f /var/log/events/scraper_cron.log"
echo ""
echo "  # Scraper loglarını görüntüle:"
echo "  tail -f /var/log/events/scraper.log"
echo ""
echo "  # Crontab'ı düzenle:"
echo "  sudo crontab -u www-data -e"
echo ""
echo "  # Crontab'ı görüntüle:"
echo "  sudo crontab -u www-data -l"
echo ""
echo "  # Veritabanındaki etkinlikleri gör:"
echo "  mongo events_db --eval 'db.events.find().limit(5).pretty()'"
echo ""
echo "🎯 Scraper her gece saat 02:00'de otomatik çalışacak!"
echo "=" * 50