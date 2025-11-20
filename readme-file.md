# 🎉 Events - Otomatik Etkinlik Scraper + Telegram Botu

Telegram üzerinden direkt mesajlaşarak etkinlik arama sistemi. **Otomatik veri toplama** (web scraping), **Gemini AI ile kategorizasyon** ve **günlük güncelleme** özellikli.

## 📋 Özellikler

- ✅ **Otomatik Web Scraping** - Biletix, Mobilet, Bubilet'ten günlük veri toplama
- ✅ **Gemini AI Entegrasyonu** - Akıllı kategorizasyon
- ✅ **Cron Job** - Her gece saat 02:00'de otomatik güncelleme
- ✅ **Telegram Bot** - Doğal dil ile etkinlik arama
- ✅ **RESTful API** - Dış entegrasyonlar için
- ✅ **MongoDB** - Hızlı ve esnek veritabanı
- ✅ **Production Ready** - Nginx, Gunicorn, Systemd

## 🏗️ Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────┐
│                    EVENTS SİSTEMİ                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                 │
│  │  Telegram    │───▶│   Flask      │                 │
│  │  Kullanıcı   │◀───│   API + Bot  │                 │
│  └──────────────┘    └───────┬──────┘                 │
│                              │                          │
│                              ▼                          │
│                      ┌──────────────┐                  │
│                      │   MongoDB    │                  │
│                      └───────┬──────┘                  │
│                              ▲                          │
│                              │                          │
│  ┌──────────────┐    ┌──────┴──────┐                  │
│  │  Cron Job    │───▶│   Scraper   │                  │
│  │  (02:00)     │    │  + Gemini   │                  │
│  └──────────────┘    └──────┬──────┘                  │
│                              │                          │
│                              ▼                          │
│              ┌────────────────────────────┐            │
│              │  Biletix  Mobilet Bubilet │            │
│              └────────────────────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Hızlı Kurulum

### 1. API Key'leri Alın

#### a) Telegram Bot Token
1. [@BotFather](https://t.me/BotFather) ile konuşun
2. `/newbot` komutu ile bot oluşturun
3. Token'ı kopyalayın: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

#### b) Gemini API Key (ÜCRETSİZ)
1. [Google AI Studio](https://makersuite.google.com/app/apikey)'ya gidin
2. "Create API Key" tıklayın
3. Key'i kopyalayın: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

### 2. Sunucuya Dosyaları Yükleyin

```bash
# Proje dizini oluştur
sudo mkdir -p /var/www/events
cd /var/www/events

# Tüm dosyaları buraya kopyalayın:
# - events_backend.py
# - scraper.py
# - requirements.txt
# - .env
# - deploy.sh
# - setup_cron.sh
# - nginx.conf
# - events.service
```

### 3. Token'ları Ekleyin

```bash
nano .env
```

Dosyayı şöyle düzenleyin:

```bash
MONGO_URI=mongodb://localhost:27017/
FLASK_ENV=production
SECRET_KEY=random-secret-key-buraya-yazin
API_PORT=5000
API_HOST=0.0.0.0

# BotFather'dan aldığınız token
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Google AI Studio'dan aldığınız key
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 4. Deploy Edin

```bash
# Deploy script'ine izin ver
chmod +x deploy.sh
chmod +x setup_cron.sh

# Deploy'u çalıştır (tüm sistemi kurar)
sudo ./deploy.sh
```

Script şunları yapacak:
- ✅ Sistem paketlerini güncelleyecek
- ✅ MongoDB'yi kuracak
- ✅ Python paketlerini yükleyecek (scraping + AI)
- ✅ Nginx'i ayarlayacak
- ✅ Telegram bot'u başlatacak
- ✅ Cron job'u kuracak (her gece saat 02:00)
- ✅ İlk scraping'i çalıştıracak

### 5. Test Edin

```bash
# Servis durumu
sudo systemctl status events

# API health check
curl http://localhost:5000/health

# Telegram bot testi
# Telegram'da botunuzu bulun ve /start yazın

# Manuel scraper testi
sudo -u www-data /var/www/events/run_scraper.sh

# Veritabanını kontrol et
mongo events_db --eval "db.events.count()"
```

## 🤖 Telegram Bot Kullanımı

### Komutlar
- `/start` - Hoşgeldin mesajı
- `/help` - Yardım

### Doğal Dil Örnekleri
- "İstanbul'da bu hafta sonu konser var mı?"
- "Ankara'da bugün tiyatro"
- "İzmir'de yarın sergi"
- "Bursa'da workshop"
- "Antalya konser"

Bot şunları anlıyor:
- **Şehirler:** İstanbul, Ankara, İzmir, Bursa, Antalya, Adana
- **Kategoriler:** Konser, Tiyatro, Sergi, Workshop, Spor, Sinema
- **Tarihler:** Bugün, Yarın, Hafta sonu, Bu hafta

## 🔍 Scraper Nasıl Çalışır?

### Otomatik Çalışma
- **Zaman:** Her gece saat 02:00
- **Kaynaklar:** Biletix, Mobilet, Bubilet
- **AI:** Gemini ile akıllı kategorizasyon
- **Temizlik:** Geçmiş etkinlikler otomatik silinir

### Manuel Çalıştırma

```bash
# Scraper'ı manuel çalıştır
sudo -u www-data /var/www/events/run_scraper.sh

# Veya Python ile direkt
cd /var/www/events
source venv/bin/activate
python3 scraper.py

# Logları izle
tail -f /var/log/events/scraper.log
tail -f /var/log/events/scraper_cron.log
```

### Scraper Ayarları

`scraper.py` dosyasında kaynaları açıp/kapayabilirsiniz:

```python
SOURCES = {
    'biletix': {'url': '...', 'enabled': True},
    'mobilet': {'url': '...', 'enabled': True},
    'bubilet': {'url': '...', 'enabled': False}  # Kapat
}
```

## 🧠 Gemini AI Entegrasyonu

### Ne İşe Yarar?
Scraping ile toplanan etkinliklerin kategorilerini otomatik belirler:

- "Duman Konseri" → `music`
- "Hamlet Oyunu" → `theater`
- "Sanat Sergisi" → `exhibition`
- "Python Workshop" → `workshop`

### API Limitleri
Google Gemini **ÜCRETSİZ** tier:
- Günde 60 istek/dakika
- Ayda 1,500 istek
- Bizim kullanım: ~50-100 istek/gece

### Gemini Olmadan Çalışır mı?
**Evet!** Gemini API key yoksa otomatik olarak basit keyword bazlı kategorizasyon kullanır.

## 📊 API Kullanımı

### Etkinlikleri Listele
```bash
GET /api/events?city=istanbul&category=music&start_date=2025-01-20&limit=10
```

### Yeni Etkinlik Ekle
```bash
POST /api/events
Content-Type: application/json

{
  "title": "Jazz Gecesi",
  "city": "istanbul",
  "category": "music",
  "date": "2025-02-15",
  "venue": "Nardis Jazz Club",
  "price": "150 TL"
}
```

### Diğer Endpoint'ler
- `GET /api/events/{id}` - Tek etkinlik
- `PUT /api/events/{id}` - Güncelle
- `DELETE /api/events/{id}` - Sil
- `GET /api/cities` - Şehir listesi
- `GET /api/categories` - Kategori listesi
- `GET /health` - Sistem sağlığı

## 🛠️ Yararlı Komutlar

### Servis Yönetimi
```bash
# Servisi yeniden başlat (API + Bot)
sudo systemctl restart events

# Durumu kontrol et
sudo systemctl status events

# Logları izle
sudo journalctl -u events -f
```

### Scraper Yönetimi
```bash
# Manuel çalıştır
sudo -u www-data /var/www/events/run_scraper.sh

# Scraper logları
tail -f /var/log/events/scraper.log

# Cron logları
tail -f /var/log/events/scraper_cron.log

# Cron job'u düzenle
sudo crontab -u www-data -e

# Cron job'u görüntüle
sudo crontab -u www-data -l
```

### Veritabanı
```bash
# MongoDB'ye bağlan
mongo events_db

# Etkinlik sayısı
db.events.count()

# Son eklenen 10 etkinlik
db.events.find().sort({created_at: -1}).limit(10).pretty()

# Şehirlere göre grup
db.events.aggregate([{$group: {_id: "$city", count: {$sum: 1}}}])

# Kategorilere göre grup
db.events.aggregate([{$group: {_id: "$category", count: {$sum: 1}}}])

# Veritabanını temizle
db.events.deleteMany({})
```

### Nginx
```bash
# Nginx'i yeniden başlat
sudo systemctl restart nginx

# Konfigürasyonu test et
sudo nginx -t

# Access logları
tail -f /var/log/nginx/events_access.log

# Error logları
tail -f /var/log/nginx/events_error.log
```

## 🔒 Güvenlik

### Firewall
```bash
sudo ufw enable
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
```

### SSL/HTTPS
```bash
# Certbot yükle
sudo apt-get install certbot python3-certbot-nginx

# SSL sertifikası al
sudo certbot --nginx -d your-domain.com

# Otomatik yenileme test
sudo certbot renew --dry-run
```

### API Rate Limiting
Nginx konfigürasyonunda aktif:
- Saniyede 10 istek
- Burst: 20 istek

## 📈 Monitoring

### Sistem Sağlığı
```bash
# Tüm servisler
sudo systemctl status events mongodb nginx

# API health
curl http://localhost:5000/health

# Disk kullanımı
df -h

# RAM
free -m

# CPU
top
```

### Scraper İstatistikleri
```bash
# Son scraping sonucu
tail -20 /var/log/events/scraper.log

# Scraping geçmişi
grep "Scraper tamamlandı" /var/log/events/scraper.log

# Hata sayısı
grep "ERROR" /var/log/events/scraper.log | wc -l
```

## 🐛 Sorun Giderme

### Scraper Çalışmıyor

1. **Cron job kontrol:**
```bash
sudo crontab -u www-data -l
```

2. **Manuel çalıştır ve logları izle:**
```bash
sudo -u www-data /var/www/events/run_scraper.sh
tail -f /var/log/events/scraper.log
```

3. **Gemini API key'i kontrol:**
```bash
cat /var/www/events/.env | grep GEMINI_API_KEY
```

### Telegram Bot Yanıt Vermiyor

1. **Token kontrol:**
```bash
cat /var/www/events/.env | grep TELEGRAM_BOT_TOKEN
```

2. **Servis durumu:**
```bash
sudo systemctl status events
sudo journalctl -u events -f
```

3. **Manuel test:**
```bash
cd /var/www/events
source venv/bin/activate
python3 events_backend.py
```

### Veritabanı Boş

1. **Scraper'ı çalıştır:**
```bash
sudo -u www-data /var/www/events/run_scraper.sh
```

2. **Örnek veri ekle:**
```bash
curl -X POST http://localhost:5000/api/seed
```

3. **Manuel veri ekle:**
```bash
curl -X POST http://localhost:5000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Etkinlik",
    "city": "istanbul",
    "category": "music",
    "date": "2025-12-31",
    "venue": "Test Mekan",
    "price": "100 TL"
  }'
```

### Gemini API Limiti

Eğer günlük limit doluysa, scraper otomatik olarak basit kategorizasyon kullanacaktır. Limit yenilenene kadar bekleyin veya API key'i yükseltin.

## 📁 Proje Yapısı

```
/var/www/events/
├── events_backend.py                    # Flask API + Telegram Bot
├── scraper.py                # Web Scraper + Gemini AI
├── requirements.txt          # Python bağımlılıkları
├── .env                      # Çevre değişkenleri (TOKEN'lar)
├── run_scraper.sh           # Cron için scraper script
├── venv/                     # Python sanal ortamı
└── logs/                     # Log dosyaları

/etc/nginx/
└── sites-available/
    └── events               # Nginx konfigürasyonu

/etc/systemd/system/
└── events.service           # Systemd service

/var/log/events/
├── scraper.log              # Scraper logları
├── scraper_cron.log         # Cron job logları
├── access.log               # API access logları
└── error.log                # API error logları
```

## 🎯 Özellik Karşılaştırması

| Özellik | Durum |
|---------|-------|
| Telegram Bot | ✅ Aktif |
| RESTful API | ✅ Aktif |
| Otomatik Scraping | ✅ Aktif (02:00) |
| Gemini AI | ✅ Aktif |
| MongoDB | ✅ Aktif |
| Cron Job | ✅ Aktif |
| Nginx | ✅ Aktif |
| SSL/HTTPS | ⚙️ Opsiyonel |
| N8n | ❌ Kaldırıldı |

## 💡 İpuçları

- **Scraping Zamanı:** Gece 02:00 ideal çünkü trafik azdır. Değiştirmek için crontab'ı düzenleyin.
- **Rate Limiting:** Scraper her site arasında 1 saniye bekler (rate limit ihlali önlemek için).
- **Gemini Limiti:** Ücretsiz tier yeterlidir. Gerekirse basit kategorizasyon fallback olarak çalışır.
- **Veritabanı Boyutu:** MongoDB otomatik olarak eski etkinlikleri temizler.
- **Backup:** MongoDB verilerini düzenli yedekleyin: `mongodump --db events_db`

## 🤝 Katkıda Bulunma

Yeni scraping kaynağı eklemek için `scraper.py` dosyasında:

1. Yeni scrape fonksiyonu ekle: `scrape_yeni_site()`
2. `SOURCES` dict'ine ekle
3. `run_scraper()` fonksiyonunda çağır

## 📄 Lisans

MIT License

---

**Kurulum Checklist:**

- [ ] Telegram bot token alındı
- [ ] Gemini API key alındı
- [ ] Token'lar `.env` dosyasına eklendi
- [ ] `deploy.sh` çalıştırıldı
- [ ] MongoDB çalışıyor
- [ ] Events service çalışıyor
- [ ] Nginx çalışıyor
- [ ] Cron job kuruldu
- [ ] İlk scraping başarılı
- [ ] Telegram bot test edildi
- [ ] Veritabanında etkinlikler var

Hepsi ✅ ise sisteminiz hazır! 🎉

## 📋 Özellikler

- ✅ Telegram üzerinden doğrudan mesajlaşma
- ✅ Doğal dil işleme - "İstanbul'da bu hafta sonu konser var mı?" gibi sorular
- ✅ Şehir, kategori ve tarih bazlı akıllı filtreleme
- ✅ RESTful API (opsiyonel entegrasyonlar için)
- ✅ MongoDB veritabanı
- ✅ Tek sunucuda hem API hem bot çalışır
- ✅ Production-ready deployment
- ✅ Systemd service ile otomatik yeniden başlatma

## 🚀 Hızlı Kurulum

### 1. Telegram Bot Oluşturun

İlk önce Telegram botunuzu oluşturun:

1. Telegram'da [@BotFather](https://t.me/BotFather)'ı açın
2. `/newbot` komutunu gönderin
3. Bot için bir isim verin (örn: "Events Etkinlik Botu")
4. Bot için bir username verin (örn: "events_events_bot")
5. Size verilen **bot token**'ı kaydedin (örn: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Sunucu Gereksinimlerini Yükleyin

```bash
# Ubuntu/Debian için
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx mongodb git
```

### 3. Projeyi Kurun

```bash
# Proje dizini oluştur
sudo mkdir -p /var/www/events
cd /var/www/events

# Dosyaları buraya kopyalayın
# events_backend.py, requirements.txt, .env, deploy.sh, nginx.conf, events.service
```

### 4. Bot Token'ı Ekleyin

`.env` dosyasını düzenleyin:

```bash
nano .env
```

`TELEGRAM_BOT_TOKEN` satırına BotFather'dan aldığınız token'ı ekleyin:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 5. Deployment Script'i Çalıştırın

```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

Bu script:
- Sistem paketlerini güncelleyecek
- MongoDB'yi kurup başlatacak
- Python sanal ortamı oluşturacak
- Telegram bot kütüphanesini yükleyecek
- Nginx'i yapılandıracak
- Systemd service'i oluşturacak
- Hem API'yi hem Telegram botunu başlatacak
- Örnek verilerle veritabanını dolduracak

### 6. Testi Yapın

```bash
# Servis durumunu kontrol edin
sudo systemctl status events

# Logları izleyin
sudo journalctl -u events -f

# Telegram'da botunuzu bulun ve /start yazın
```

## 🤖 Telegram Bot Kullanımı

Botunuzu Telegram'da bulun ve mesaj gönderin:

### Komutlar

- `/start` - Botu başlat, hoşgeldin mesajı
- `/help` - Yardım mesajı

### Doğal Dil Örnekleri

Bot şu tarz mesajları anlayabilir:

- "İstanbul'da bu hafta sonu konser var mı?"
- "Ankara'da bugün tiyatro"
- "İzmir'de yarın sergi"
- "Bursa'da workshop"
- "Antalya'da hafta sonu ne var?"
- "İstanbul konser"
- "Ankara tiyatro bu hafta"

### Bot Ne Anlıyor?

**Şehirler:**
- İstanbul, Ankara, İzmir, Bursa, Antalya, Adana

**Kategoriler:**
- Konser/Müzik → `music`
- Tiyatro → `theater`
- Sergi → `exhibition`
- Workshop/Atölye → `workshop`
- Spor → `sports`
- Sinema/Film → `cinema`

**Tarihler:**
- "bugün" → Bugün
- "yarın" → Yarın
- "hafta sonu" → Cumartesi-Pazar
- "bu hafta" → Haftanın geri kalanı
- Belirtilmezse → Önümüzdeki 7 gün

## 📡 API Kullanımı (Opsiyonel)

API hala çalışıyor, dış entegrasyonlar için kullanabilirsiniz:

### Etkinlikleri Listele

```bash
GET /api/events?city=istanbul&category=music&start_date=2025-01-20&end_date=2025-01-27
```

### Yeni Etkinlik Ekle

```bash
POST /api/events
Content-Type: application/json

{
  "title": "Jazz Gecesi",
  "city": "istanbul",
  "category": "music",
  "date": "2025-02-15",
  "time": "21:00",
  "venue": "Nardis Jazz Club",
  "price": "150 TL"
}
```

Diğer endpoint'ler için önceki README'ye bakın.

## 🛠️ Yararlı Komutlar

### Servisi Yönet

```bash
# Servisi yeniden başlat (hem API hem bot)
sudo systemctl restart events

# Durumu kontrol et
sudo systemctl status events

# Logları canlı izle
sudo journalctl -u events -f

# Servisi durdur
sudo systemctl stop events

# Servisi başlat
sudo systemctl start events
```

### Bot Loglarını İzle

```bash
# Tüm loglar
sudo journalctl -u events -f

# Sadece Telegram bot logları (filter)
sudo journalctl -u events -f | grep -i telegram

# Son 100 satır
sudo journalctl -u events -n 100
```

### Nginx'i Yönet

```bash
# Nginx'i yeniden başlat
sudo systemctl restart nginx

# Konfigürasyonu test et
sudo nginx -t

# Logları görüntüle
sudo tail -f /var/log/nginx/events_access.log
```

### MongoDB

```bash
# MongoDB'ye bağlan
mongo

# Veritabanını kullan
use events_db

# Etkinlikleri listele
db.events.find().pretty()

# Örnek verilerle doldur (API üzerinden)
curl -X POST http://localhost:5000/api/seed
```

## 🐛 Sorun Giderme

### Bot Mesajlara Cevap Vermiyor

1. **Token'ı kontrol edin:**
```bash
cat /var/www/events/.env | grep TELEGRAM_BOT_TOKEN
```

2. **Servisi yeniden başlatın:**
```bash
sudo systemctl restart events
```

3. **Logları kontrol edin:**
```bash
sudo journalctl -u events -f
```

4. **BotFather'da bot token'ının doğru olduğunu kontrol edin**

### "Update 'NoneType' caused error" Hatası

Bu normal, bazı Telegram güncellemeleri işlenmeyebilir. Kritik değil.

### Veritabanı Boş

```bash
# Örnek verilerle doldur
curl -X POST http://localhost:5000/api/seed

# Veya manuel ekle
curl -X POST http://localhost:5000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Etkinlik",
    "city": "istanbul",
    "category": "music",
    "date": "2025-12-31",
    "venue": "Test Venue",
    "price": "100 TL"
  }'
```

### Bot Çok Yavaş Yanıt Veriyor

1. **MongoDB index'lerini kontrol edin:**
```bash
mongo events_db --eval "db.events.getIndexes()"
```

2. **Sunucu kaynaklarını kontrol edin:**
```bash
htop
df -h
free -m
```

### Telegram'da Bot Bulunamıyor

- BotFather'da oluşturduğunuz username'i doğru yazın
- Username `@` ile başlamalı: `@events_events_bot`
- Botunuz public olmalı (BotFather'da ayarları kontrol edin)

## 🔒 Güvenlik

### Rate Limiting

Nginx konfigürasyonunda rate limiting aktif:
- Saniyede 10 istek
- Burst: 20 istek

### Firewall

```bash
sudo ufw enable
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
```

### SSL/HTTPS (Önerilen)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📊 Monitoring

### Sistem Sağlığı

```bash
# API health check
curl http://localhost:5000/health

# Servis durumu
sudo systemctl status events mongodb nginx

# Disk kullanımı
df -h

# RAM kullanımı
free -m

# CPU kullanımı
top
```

### Telegram Bot İstatistikleri

Loglardan kullanıcı aramalarını görebilirsiniz:

```bash
sudo journalctl -u events | grep "User.*searched"
```

## 📁 Proje Yapısı

```
/var/www/events/
├── events_backend.py                 # Ana uygulama (API + Bot)
├── requirements.txt       # Python bağımlılıkları
├── .env                   # Çevre değişkenleri (TOKEN buradadır!)
├── venv/                  # Python sanal ortamı
└── logs/                  # Log dosyaları

/etc/nginx/
└── sites-available/
    └── events            # Nginx konfigürasyonu

/etc/systemd/system/
└── events.service        # Systemd service
```

## 🎯 Özellikler ve Sınırlamalar

### ✅ Çalışıyor

- ✅ Telegram direkt mesajlaşma
- ✅ Doğal dil anlama
- ✅ Şehir, kategori, tarih filtreleme
- ✅ Markdown formatında güzel mesajlar
- ✅ Emoji desteği
- ✅ RESTful API
- ✅ MongoDB tam-metin araması
- ✅ Error handling

### 🔄 Gelecek Özellikler (İstersen Ekleyebiliriz)

- ⏳ Kullanıcı favori etkinlikler
- ⏳ Etkinlik bildirimleri (yeni etkinlik eklendiğinde)
- ⏳ Inline keyboard ile interaktif seçim
- ⏳ Lokasyon bazlı arama
- ⏳ Çoklu dil desteği
- ⏳ Admin paneli

## 💡 N8n vs Direkt Entegrasyon

### Neden N8n'i Kaldırdık?

| Özellik | N8n ile | Direkt Entegrasyon |
|---------|---------|-------------------|
| **Karmaşıklık** | Yüksek (3 sistem) | Düşük (1 sistem) |
| **Hız** | Yavaş (network hop'ları) | Hızlı (direkt) |
| **Bakım** | Zor (3 sistem) | Kolay (1 sistem) |
| **Maliyet** | Fazla RAM/CPU | Az kaynak |
| **Esneklik** | Orta | Yüksek |

Direkt entegrasyon ile:
- ✅ Daha hızlı yanıt süresi
- ✅ Daha az sunucu kaynağı
- ✅ Daha az karmaşıklık
- ✅ Daha kolay debug
- ✅ Tek bir kod tabanı

## 🤝 Katkıda Bulunma

Pull request'ler kabul edilir. Büyük değişiklikler için önce issue açın.

## 📄 Lisans

MIT License

## 📞 Destek

Sorun yaşıyorsanız:
1. Logları kontrol edin: `sudo journalctl -u events -f`
2. Issue açın
3. Telegram: @your_support_channel (varsa)

---

**Son Kontrol Listesi:**

- [ ] MongoDB çalışıyor mu? `sudo systemctl status mongodb`
- [ ] Bot token `.env` dosyasında mı?
- [ ] Servis çalışıyor mu? `sudo systemctl status events`
- [ ] Nginx çalışıyor mu? `sudo systemctl status nginx`
- [ ] Örnek veriler yüklendi mi? `curl -X POST http://localhost:5000/api/seed`
- [ ] Telegram'da bot bulunuyor mu? `@your_bot_username`
- [ ] `/start` komutu çalışıyor mu?

Hepsi ✅ ise sisteminiz hazır! 🎉