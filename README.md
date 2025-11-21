# 🎉 Events - Antalya Etkinlik Bulucu

**Telegram Bot + Web Arayüzü** ile Antalya etkinliklerini bulun. **RAG (Retrieval-Augmented Generation)** sistemi ile doğal dil işleme, **otomatik web scraping** ve **günlük güncelleme** özellikli.

## 📋 Özellikler

✅ **Web Arayüzü** - Modern chat interface (http://events.tugrul.app)

✅ **Telegram Bot** - Doğal dil ile etkinlik arama

✅ **RAG Sistemi** - Semantic search ile akıllı etkinlik bulma (Sentence-Transformers + FAISS + Gemini)

✅ **Otomatik Web Scraping** - Biletinial ve BUBilet'ten günlük veri toplama (Antalya)

✅ **Gemini AI** - Akıllı kategorizasyon ve doğal dil yanıtları

✅ **Cron Job** - Her gece saat 02:00'de otomatik güncelleme + embeddings refresh

✅ **RESTful API** - Dış entegrasyonlar için

✅ **MongoDB** - Hızlı ve esnek veritabanı

✅ **Production Ready** - Nginx, Gunicorn, Systemd

## 🏗️ Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────┐
│                    EVENTS SİSTEMİ                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                 │
│  │  Telegram    │───▶│              │                 │
│  │  Kullanıcı   │    │   Flask      │                 │
│  └──────────────┘    │   API + Bot  │                 │
│                      │              │                  │
│  ┌──────────────┐    │              │                 │
│  │  Web         │───▶│              │                 │
│  │  Arayüzü     │    │   (Port 5001)│                 │
│  └──────────────┘    └───────┬──────┘                 │
│                              │                          │
│                              ▼                          │
│                      ┌──────────────┐                  │
│                      │   MongoDB    │                  │
│                      │   + FAISS    │                  │
│                      │  (Embeddings)│                  │
│                      └───────┬──────┘                  │
│                              ▲                          │
│                              │                          │
│  ┌──────────────┐    ┌──────┴──────┐                  │
│  │  Cron Job    │───▶│   Scraper   │                  │
│  │  (02:00)     │    │  + Gemini   │                  │
│  └──────────────┘    │  + RAG      │                  │
│                      └──────┬──────┘                  │
│                              │                          │
│                              ▼                          │
│              ┌────────────────────────────┐            │
│              │  Biletinial  BUBilet      │            │
│              └────────────────────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 🌐 Erişim Noktaları

- **Web Arayüzü**: http://events.tugrul.app
- **API**: http://events.tugrul.app/api
- **Health Check**: http://events.tugrul.app/health
- **Telegram Bot**: Telegram'da botunuzu bulun

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

# Git'ten clone edin veya dosyaları kopyalayın:
# - events_backend.py
# - scraper-script.py
# - rag_engine.py
# - rag_retriever.py
# - requirements.txt
# - web/index.html
# - deploy-script.sh
# - cron-setup.sh
# - nginx-config.txt
# - systemd-service.txt
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
API_PORT=5001
API_HOST=0.0.0.0

# BotFather'dan aldığınız token
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Google AI Studio'dan aldığınız key
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 4. Deploy Edin

```bash
# Deploy script'ine izin ver
chmod +x deploy-script.sh
chmod +x cron-setup.sh

# Deploy'u çalıştır (tüm sistemi kurar)
sudo ./deploy-script.sh
```

Script şunları yapacak:

- ✅ Sistem paketlerini güncelleyecek
- ✅ MongoDB'yi kuracak
- ✅ Python paketlerini yükleyecek (scraping + AI + RAG)
- ✅ Nginx'i ayarlayacak (web arayüzü + API)
- ✅ Telegram bot'u başlatacak
- ✅ Cron job'u kuracak (her gece saat 02:00)
- ✅ İlk scraping'i çalıştıracak
- ✅ RAG embeddings'leri oluşturacak

### 5. Test Edin

```bash
# Servis durumu
sudo systemctl status events

# API health check
curl http://localhost:5001/health

# Web arayüzü
curl http://localhost:5001/

# Telegram bot testi
# Telegram'da botunuzu bulun ve /start yazın

# Manuel scraper testi
sudo -u www-data /var/www/events/run_scraper.sh

# Veritabanını kontrol et
mongo events_db --eval "db.events.count()"
```

## 🌐 Web Arayüzü Kullanımı

### Erişim

Web arayüzüne tarayıcınızdan erişin:

```
http://events.tugrul.app
```

veya sunucu IP'si ile:

```
http://65.21.182.26
```

### Özellikler

- ✅ **Modern Chat Interface** - Telegram benzeri kullanıcı deneyimi
- ✅ **Doğal Dil Sorguları** - "Bu hafta sonu konser var mı?" gibi sorular
- ✅ **RAG Sistemi** - Semantic search ile akıllı etkinlik bulma
- ✅ **Hızlı Örnekler** - Tek tıkla örnek sorgular
- ✅ **Responsive Design** - Mobil ve masaüstü uyumlu

### Örnek Sorgular

- "Bu hafta sonu konser var mı?"
- "Kasım ayı etkinlikleri"
- "Bugün tiyatro"
- "Yarın sinema"
- "19 ekim konser"

## 🤖 Telegram Bot Kullanımı

### Komutlar

- `/start` - Hoşgeldin mesajı
- `/help` - Yardım

### Doğal Dil Örnekleri

Bot şu tarz mesajları anlayabilir:

- "Bu hafta sonu konser var mı?"
- "Kasım ayı etkinlikleri"
- "Bugün tiyatro"
- "Yarın sinema"

**Not:** Bot şu anda sadece **Antalya** etkinlikleri için çalışmaktadır.

## 🧠 RAG (Retrieval-Augmented Generation) Sistemi

### Nasıl Çalışır?

1. **Embedding Oluşturma**: Etkinlikler Sentence-Transformers ile vektörlere dönüştürülür
2. **FAISS Index**: Embeddings FAISS vector database'de saklanır
3. **Semantic Search**: Kullanıcı sorgusu da embedding'e dönüştürülür ve benzer etkinlikler bulunur
4. **Gemini AI**: Bulunan etkinlikler Gemini AI ile doğal dil yanıtına dönüştürülür

### Avantajlar

- ✅ **Semantic Search** - Sadece keyword değil, anlam bazlı arama
- ✅ **Hızlı** - FAISS ile milisaniyeler içinde sonuç
- ✅ **Akıllı** - Gemini AI ile doğal dil yanıtları
- ✅ **Otomatik** - Embeddings scraper sonrası otomatik güncellenir

### Embeddings Güncelleme

Embeddings otomatik olarak:
- Backend başladığında
- İlk sorguda
- Scraper çalıştıktan sonra backend yeniden başlatıldığında

güncellenir.

## 🔍 Scraper Nasıl Çalışır?

### Otomatik Çalışma

- **Zaman:** Her gece saat 02:00
- **Kaynaklar:** Biletinial, BUBilet (Antalya)
- **AI:** Gemini ile akıllı kategorizasyon
- **RAG:** Embeddings otomatik güncellenir
- **Temizlik:** Geçmiş etkinlikler otomatik silinir

### Manuel Çalıştırma

```bash
# Scraper'ı manuel çalıştır
sudo -u www-data /var/www/events/run_scraper.sh

# Veya Python ile direkt
cd /var/www/events
source venv/bin/activate
python3 scraper-script.py

# Logları izle
tail -f /var/log/events/scraper.log
tail -f /var/log/events/scraper_cron.log
```

### Scraper Ayarları

`scraper-script.py` dosyasında kaynakları açıp/kapayabilirsiniz:

```python
SCRAPERS = [
    BiletinialScraper(),  # Antalya etkinlikleri
    BUBiletScraper(),     # Antalya etkinlikleri
]
```

## 🧠 Gemini AI Entegrasyonu

### Ne İşe Yarar?

1. **Kategorizasyon**: Scraping ile toplanan etkinliklerin kategorilerini otomatik belirler
2. **RAG Yanıtları**: Semantic search sonuçlarını doğal dil yanıtına dönüştürür

### API Limitleri

Google Gemini **ÜCRETSİZ** tier:

- Günde 60 istek/dakika
- Ayda 1,500 istek
- Bizim kullanım: ~50-100 istek/gece (scraping) + kullanıcı sorguları

### Gemini Olmadan Çalışır mı?

**Evet!** Gemini API key yoksa otomatik olarak basit keyword bazlı kategorizasyon kullanır.

## 📊 API Kullanımı

### Web Chat API

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Bu hafta sonu konser var mı?"
}
```

Yanıt:

```json
{
  "success": true,
  "answer": "Merhaba! Antalya'da bu hafta sonu için..."
}
```

### Etkinlikleri Listele

```bash
GET /api/events?city=antalya&category=music&start_date=2025-01-20&limit=10
```

### Yeni Etkinlik Ekle

```bash
POST /api/events
Content-Type: application/json

{
  "title": "Jazz Gecesi",
  "city": "antalya",
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
# Servisi yeniden başlat (API + Bot + Web)
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
sudo certbot --nginx -d events.tugrul.app

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
curl http://localhost:5001/health

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

### Web Arayüzü Çalışmıyor

1. **Nginx kontrol:**

```bash
sudo systemctl status nginx
sudo nginx -t
```

2. **Backend kontrol:**

```bash
curl http://localhost:5001/health
curl http://localhost:5001/
```

3. **Logları kontrol:**

```bash
sudo tail -f /var/log/nginx/events_error.log
sudo journalctl -u events -f
```

### Veritabanı Boş

1. **Scraper'ı çalıştır:**

```bash
sudo -u www-data /var/www/events/run_scraper.sh
```

2. **Örnek veri ekle:**

```bash
curl -X POST http://localhost:5001/api/seed
```

3. **Manuel veri ekle:**

```bash
curl -X POST http://localhost:5001/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Etkinlik",
    "city": "antalya",
    "category": "music",
    "date": "2025-12-31",
    "venue": "Test Mekan",
    "price": "100 TL"
  }'
```

### Gemini API Limiti

Eğer günlük limit doluysa, scraper otomatik olarak basit kategorizasyon kullanacaktır. Limit yenilenene kadar bekleyin veya API key'i yükseltin.

### RAG Embeddings Oluşmuyor

1. **Backend'i yeniden başlat:**

```bash
sudo systemctl restart events
```

2. **Manuel oluştur:**

```bash
cd /var/www/events
source venv/bin/activate
python3 -c "from rag_engine import get_rag_engine; get_rag_engine()"
```

## 📁 Proje Yapısı

```
/var/www/events/
├── events_backend.py          # Flask API + Telegram Bot + Web
├── scraper-script.py          # Web Scraper + Gemini AI
├── rag_engine.py              # RAG engine (Gemini + Semantic Search)
├── rag_retriever.py           # FAISS retriever
├── requirements.txt           # Python bağımlılıkları
├── .env                       # Çevre değişkenleri (TOKEN'lar)
├── run_scraper.sh            # Cron için scraper script
├── web/
│   └── index.html            # Web arayüzü
├── venv/                     # Python sanal ortamı
└── logs/                     # Log dosyaları

/etc/nginx/
└── sites-available/
    └── events                # Nginx konfigürasyonu

/etc/systemd/system/
└── events.service            # Systemd service

/var/log/events/
├── scraper.log               # Scraper logları
├── scraper_cron.log          # Cron job logları
├── access.log                # API access logları
└── error.log                 # API error logları
```

## 🎯 Özellik Karşılaştırması

| Özellik          | Durum            |
| ---------------- | ---------------- |
| Web Arayüzü      | ✅ Aktif         |
| Telegram Bot     | ✅ Aktif         |
| RAG Sistemi      | ✅ Aktif         |
| RESTful API      | ✅ Aktif         |
| Otomatik Scraping| ✅ Aktif (02:00) |
| Gemini AI        | ✅ Aktif         |
| MongoDB          | ✅ Aktif         |
| FAISS            | ✅ Aktif         |
| Cron Job         | ✅ Aktif         |
| Nginx            | ✅ Aktif         |
| SSL/HTTPS         | ⚙️ Opsiyonel   |

## 💡 İpuçları

- **Scraping Zamanı:** Gece 02:00 ideal çünkü trafik azdır. Değiştirmek için crontab'ı düzenleyin.
- **Rate Limiting:** Scraper her site arasında 1 saniye bekler (rate limit ihlali önlemek için).
- **Gemini Limiti:** Ücretsiz tier yeterlidir. Gerekirse basit kategorizasyon fallback olarak çalışır.
- **Veritabanı Boyutu:** MongoDB otomatik olarak eski etkinlikleri temizler.
- **RAG Embeddings:** Backend başladığında veya scraper sonrası otomatik güncellenir.
- **Backup:** MongoDB verilerini düzenli yedekleyin: `mongodump --db events_db`

## 🤝 Katkıda Bulunma

Yeni scraping kaynağı eklemek için `scraper-script.py` dosyasında:

1. Yeni scraper class'ı ekle: `class YeniSiteScraper(BaseEventScraper)`
2. `SCRAPERS` listesine ekle
3. Test et

## 📄 Lisans

MIT License

---

**Kurulum Checklist:**

- [ ] Telegram bot token alındı
- [ ] Gemini API key alındı
- [ ] Token'lar `.env` dosyasına eklendi
- [ ] `deploy-script.sh` çalıştırıldı
- [ ] MongoDB çalışıyor
- [ ] Events service çalışıyor
- [ ] Nginx çalışıyor
- [ ] Cron job kuruldu
- [ ] İlk scraping başarılı
- [ ] RAG embeddings oluşturuldu
- [ ] Web arayüzü erişilebilir (http://events.tugrul.app)
- [ ] Telegram bot test edildi
- [ ] Veritabanında etkinlikler var

Hepsi ✅ ise sisteminiz hazır! 🎉

