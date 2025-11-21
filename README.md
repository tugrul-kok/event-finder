# 🎉 Events - Antalya Event Finder

**Telegram Bot + Web Interface** for finding events in Antalya. Features **RAG (Retrieval-Augmented Generation)** system with natural language processing, **automatic web scraping**, and **daily updates**.

## 📋 Features

✅ **Web Interface** - Modern chat interface (http://events.tugrul.app)

✅ **Telegram Bot** - Natural language event search

✅ **RAG System** - Intelligent event finding with semantic search (Sentence-Transformers + FAISS + Gemini)

✅ **Automatic Web Scraping** - Daily data collection from Biletinial and BUBilet (Antalya)

✅ **Gemini AI** - Smart categorization and natural language responses

✅ **Cron Job** - Automatic daily update at 02:00 + embeddings refresh

✅ **RESTful API** - For external integrations

✅ **MongoDB** - Fast and flexible database

✅ **Production Ready** - Nginx, Gunicorn, Systemd

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EVENTS SYSTEM                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                 │
│  │  Telegram    │───▶│              │                 │
│  │  User        │    │   Flask      │                 │
│  └──────────────┘    │   API + Bot  │                 │
│                      │              │                  │
│  ┌──────────────┐    │              │                 │
│  │  Web         │───▶│              │                 │
│  │  Interface   │    │   (Port 5001)│                 │
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
│              │  Biletinial  BUBilet        │            │
│              └────────────────────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 🌐 Access Points

- **Web Interface**: http://events.tugrul.app
- **API**: http://events.tugrul.app/api
- **Health Check**: http://events.tugrul.app/health
- **Telegram Bot**: Find your bot on Telegram

## 🚀 Quick Setup

### 1. Get API Keys

#### a) Telegram Bot Token

1. Talk to [@BotFather](https://t.me/BotFather)
2. Create a bot with `/newbot` command
3. Copy the token: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

#### b) Gemini API Key (FREE)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

### 2. Upload Files to Server

```bash
# Create project directory
sudo mkdir -p /var/www/events
cd /var/www/events

# Clone from Git or copy files:
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

### 3. Add Tokens

```bash
nano .env
```

Edit the file:

```bash
MONGO_URI=mongodb://localhost:27017/
FLASK_ENV=production
SECRET_KEY=random-secret-key-here
API_PORT=5001
API_HOST=0.0.0.0

# Token from BotFather
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Key from Google AI Studio
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 4. Deploy

```bash
# Give execute permission to deploy script
chmod +x deploy-script.sh
chmod +x cron-setup.sh

# Run deployment (installs entire system)
sudo ./deploy-script.sh
```

The script will:

- ✅ Update system packages
- ✅ Install MongoDB
- ✅ Install Python packages (scraping + AI + RAG)
- ✅ Configure Nginx (web interface + API)
- ✅ Start Telegram bot
- ✅ Setup cron job (every night at 02:00)
- ✅ Run first scraping
- ✅ Create RAG embeddings

### 5. Test

```bash
# Service status
sudo systemctl status events

# API health check
curl http://localhost:5001/health

# Web interface
curl http://localhost:5001/

# Telegram bot test
# Find your bot on Telegram and send /start

# Manual scraper test
sudo -u www-data /var/www/events/run_scraper.sh

# Check database
mongo events_db --eval "db.events.count()"
```

## 🌐 Web Interface Usage

### Access

Access the web interface from your browser:

```
http://events.tugrul.app
```

or with server IP:

```
http://65.21.182.26
```

### Features

- ✅ **Modern Chat Interface** - Telegram-like user experience
- ✅ **Natural Language Queries** - Ask questions like "Are there any concerts this weekend?"
- ✅ **RAG System** - Intelligent event finding with semantic search
- ✅ **Quick Examples** - One-click example queries
- ✅ **Responsive Design** - Mobile and desktop compatible

### Example Queries

- "Are there any concerts this weekend?"
- "November events"
- "Theater today"
- "Cinema tomorrow"
- "October 19 concert"

## 🤖 Telegram Bot Usage

### Commands

- `/start` - Welcome message
- `/help` - Help

### Natural Language Examples

The bot can understand messages like:

- "Are there any concerts this weekend?"
- "November events"
- "Theater today"
- "Cinema tomorrow"

**Note:** The bot currently works only for **Antalya** events.

## 🧠 RAG (Retrieval-Augmented Generation) System

### How It Works

1. **Embedding Creation**: Events are converted to vectors using Sentence-Transformers
2. **FAISS Index**: Embeddings are stored in FAISS vector database
3. **Semantic Search**: User query is also converted to embedding and similar events are found
4. **Gemini AI**: Found events are converted to natural language response using Gemini AI

### Advantages

- ✅ **Semantic Search** - Meaning-based search, not just keywords
- ✅ **Fast** - Results in milliseconds with FAISS
- ✅ **Smart** - Natural language responses with Gemini AI
- ✅ **Automatic** - Embeddings are automatically updated after scraper runs

### Embedding Updates

Embeddings are automatically updated:
- When backend starts
- On first query
- After scraper runs and backend restarts

## 🔍 How Scraper Works

### Automatic Operation

- **Time:** Every night at 02:00
- **Sources:** Biletinial, BUBilet (Antalya)
- **AI:** Smart categorization with Gemini
- **RAG:** Embeddings automatically updated
- **Cleanup:** Past events automatically deleted

### Manual Execution

```bash
# Run scraper manually
sudo -u www-data /var/www/events/run_scraper.sh

# Or directly with Python
cd /var/www/events
source venv/bin/activate
python3 scraper-script.py

# Watch logs
tail -f /var/log/events/scraper.log
tail -f /var/log/events/scraper_cron.log
```

### Scraper Settings

You can enable/disable sources in `scraper-script.py`:

```python
SCRAPERS = [
    BiletinialScraper(),  # Antalya events
    BUBiletScraper(),     # Antalya events
]
```

## 🧠 Gemini AI Integration

### What It Does

1. **Categorization**: Automatically determines categories of events collected by scraping
2. **RAG Responses**: Converts semantic search results to natural language responses

### API Limits

Google Gemini **FREE** tier:

- 60 requests/minute per day
- 1,500 requests per month
- Our usage: ~50-100 requests/night (scraping) + user queries

### Works Without Gemini?

**Yes!** If Gemini API key is missing, it automatically uses simple keyword-based categorization.

## 📊 API Usage

### Web Chat API

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Are there any concerts this weekend?"
}
```

Response:

```json
{
  "success": true,
  "answer": "Hello! For this weekend in Antalya..."
}
```

### List Events

```bash
GET /api/events?city=antalya&category=music&start_date=2025-01-20&limit=10
```

### Add New Event

```bash
POST /api/events
Content-Type: application/json

{
  "title": "Jazz Night",
  "city": "antalya",
  "category": "music",
  "date": "2025-02-15",
  "venue": "Nardis Jazz Club",
  "price": "150 TL"
}
```

### Other Endpoints

- `GET /api/events/{id}` - Single event
- `PUT /api/events/{id}` - Update
- `DELETE /api/events/{id}` - Delete
- `GET /api/cities` - City list
- `GET /api/categories` - Category list
- `GET /health` - System health

## 🛠️ Useful Commands

### Service Management

```bash
# Restart service (API + Bot + Web)
sudo systemctl restart events

# Check status
sudo systemctl status events

# Watch logs
sudo journalctl -u events -f
```

### Scraper Management

```bash
# Run manually
sudo -u www-data /var/www/events/run_scraper.sh

# Scraper logs
tail -f /var/log/events/scraper.log

# Cron logs
tail -f /var/log/events/scraper_cron.log

# Edit cron job
sudo crontab -u www-data -e

# View cron job
sudo crontab -u www-data -l
```

### Database

```bash
# Connect to MongoDB
mongo events_db

# Event count
db.events.count()

# Last 10 events
db.events.find().sort({created_at: -1}).limit(10).pretty()

# Group by city
db.events.aggregate([{$group: {_id: "$city", count: {$sum: 1}}}])

# Group by category
db.events.aggregate([{$group: {_id: "$category", count: {$sum: 1}}}])

# Clear database
db.events.deleteMany({})
```

### Nginx

```bash
# Restart Nginx
sudo systemctl restart nginx

# Test configuration
sudo nginx -t

# Access logs
tail -f /var/log/nginx/events_access.log

# Error logs
tail -f /var/log/nginx/events_error.log
```

## 🔒 Security

### Firewall

```bash
sudo ufw enable
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
```

### SSL/HTTPS

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d events.tugrul.app

# Test automatic renewal
sudo certbot renew --dry-run
```

### API Rate Limiting

Active in Nginx configuration:

- 10 requests per second
- Burst: 20 requests

## 📈 Monitoring

### System Health

```bash
# All services
sudo systemctl status events mongodb nginx

# API health
curl http://localhost:5001/health

# Disk usage
df -h

# RAM
free -m

# CPU
top
```

### Scraper Statistics

```bash
# Last scraping result
tail -20 /var/log/events/scraper.log

# Scraping history
grep "Scraper completed" /var/log/events/scraper.log

# Error count
grep "ERROR" /var/log/events/scraper.log | wc -l
```

## 🐛 Troubleshooting

### Scraper Not Working

1. **Check cron job:**

```bash
sudo crontab -u www-data -l
```

2. **Run manually and watch logs:**

```bash
sudo -u www-data /var/www/events/run_scraper.sh
tail -f /var/log/events/scraper.log
```

3. **Check Gemini API key:**

```bash
cat /var/www/events/.env | grep GEMINI_API_KEY
```

### Telegram Bot Not Responding

1. **Check token:**

```bash
cat /var/www/events/.env | grep TELEGRAM_BOT_TOKEN
```

2. **Service status:**

```bash
sudo systemctl status events
sudo journalctl -u events -f
```

3. **Manual test:**

```bash
cd /var/www/events
source venv/bin/activate
python3 events_backend.py
```

### Web Interface Not Working

1. **Check Nginx:**

```bash
sudo systemctl status nginx
sudo nginx -t
```

2. **Check backend:**

```bash
curl http://localhost:5001/health
curl http://localhost:5001/
```

3. **Check logs:**

```bash
sudo tail -f /var/log/nginx/events_error.log
sudo journalctl -u events -f
```

### Database Empty

1. **Run scraper:**

```bash
sudo -u www-data /var/www/events/run_scraper.sh
```

2. **Add sample data:**

```bash
curl -X POST http://localhost:5001/api/seed
```

3. **Add manually:**

```bash
curl -X POST http://localhost:5001/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Event",
    "city": "antalya",
    "category": "music",
    "date": "2025-12-31",
    "venue": "Test Venue",
    "price": "100 TL"
  }'
```

### Gemini API Limit

If daily limit is reached, scraper will automatically use simple categorization. Wait until limit resets or upgrade API key.

### RAG Embeddings Not Created

1. **Restart backend:**

```bash
sudo systemctl restart events
```

2. **Create manually:**

```bash
cd /var/www/events
source venv/bin/activate
python3 -c "from rag_engine import get_rag_engine; get_rag_engine()"
```

## 📁 Project Structure

```
/var/www/events/
├── events_backend.py          # Flask API + Telegram Bot + Web
├── scraper-script.py          # Web Scraper + Gemini AI
├── rag_engine.py              # RAG engine (Gemini + Semantic Search)
├── rag_retriever.py           # FAISS retriever
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (TOKENS)
├── run_scraper.sh            # Cron scraper script
├── web/
│   └── index.html            # Web interface
├── venv/                     # Python virtual environment
└── logs/                     # Log files

/etc/nginx/
└── sites-available/
    └── events                # Nginx configuration

/etc/systemd/system/
└── events.service            # Systemd service

/var/log/events/
├── scraper.log               # Scraper logs
├── scraper_cron.log          # Cron job logs
├── access.log                # API access logs
└── error.log                 # API error logs
```

## 🎯 Feature Comparison

| Feature          | Status            |
| ---------------- | ---------------- |
| Web Interface    | ✅ Active         |
| Telegram Bot     | ✅ Active         |
| RAG System       | ✅ Active         |
| RESTful API      | ✅ Active         |
| Auto Scraping    | ✅ Active (02:00) |
| Gemini AI        | ✅ Active         |
| MongoDB          | ✅ Active         |
| FAISS            | ✅ Active         |
| Cron Job         | ✅ Active         |
| Nginx            | ✅ Active         |
| SSL/HTTPS         | ⚙️ Optional   |

## 💡 Tips

- **Scraping Time:** 02:00 at night is ideal because traffic is low. Edit crontab to change.
- **Rate Limiting:** Scraper waits 1 second between sites (to prevent rate limit violations).
- **Gemini Limit:** Free tier is sufficient. Simple categorization works as fallback if needed.
- **Database Size:** MongoDB automatically cleans old events.
- **RAG Embeddings:** Automatically updated when backend starts or after scraper runs.
- **Backup:** Regularly backup MongoDB data: `mongodump --db events_db`

## 🤝 Contributing

To add a new scraping source in `scraper-script.py`:

1. Add new scraper class: `class NewSiteScraper(BaseEventScraper)`
2. Add to `SCRAPERS` list
3. Test

## 📄 License

MIT License

---

**Installation Checklist:**

- [ ] Telegram bot token obtained
- [ ] Gemini API key obtained
- [ ] Tokens added to `.env` file
- [ ] `deploy-script.sh` executed
- [ ] MongoDB running
- [ ] Events service running
- [ ] Nginx running
- [ ] Cron job installed
- [ ] First scraping successful
- [ ] RAG embeddings created
- [ ] Web interface accessible (http://events.tugrul.app)
- [ ] Telegram bot tested
- [ ] Events in database

All ✅ means your system is ready! 🎉
