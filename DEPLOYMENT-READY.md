# ✅ Deployment Ready Checklist

## What's Included

### ✅ Web Interface
- **URL**: http://events.tugrul.app
- **Features**: Chat interface, same RAG system as Telegram
- **File**: `web/index.html`

### ✅ Telegram Bot
- Same backend, works via Telegram
- Uses same RAG engine and database

### ✅ Backend API
- Flask API on port 5001
- Serves web interface and API endpoints
- RAG system with embeddings

### ✅ Auto-Scraping
- **Time**: Every day at 02:00
- **Actions**:
  1. Scrapes events from Biletinial & BUBilet
  2. Saves to MongoDB
  3. Restarts backend to refresh RAG embeddings

### ✅ Server Configuration
- **IP**: 65.21.182.26
- **Domain**: events.tugrul.app
- **Nginx**: Reverse proxy configured
- **Systemd**: Service configured
- **Cron**: Daily scraping configured

## Files Ready for Deployment

### Core Files
- ✅ `events_backend.py` - Main backend (Flask + Telegram + Web)
- ✅ `scraper-script.py` - Event scraper
- ✅ `rag_engine.py` - RAG engine
- ✅ `rag_retriever.py` - FAISS retriever
- ✅ `requirements.txt` - Dependencies
- ✅ `web/index.html` - Web interface

### Deployment Files
- ✅ `deploy-script.sh` - Main deployment script
- ✅ `cron-setup.sh` - Cron job setup
- ✅ `systemd-service.txt` - Systemd service config
- ✅ `nginx-config.txt` - Nginx config template (deploy script creates actual config)

### Configuration
- ✅ `env-file.sh` - Environment variables template
- ✅ `.gitignore` - Git ignore rules

## Deployment Steps

### 1. Upload to Server

```bash
# From local machine
cd /Users/tugrul/Desktop/amean/events
scp -r * root@65.21.182.26:/tmp/events-deploy/
```

### 2. Run Deployment

```bash
# SSH to server
ssh root@65.21.182.26
cd /tmp/events-deploy
chmod +x deploy-script.sh
sudo ./deploy-script.sh
```

### 3. Configure .env

```bash
nano /var/www/events/.env
```

Add your API keys (TELEGRAM_BOT_TOKEN, GEMINI_API_KEY)

### 4. Restart Services

```bash
sudo systemctl restart events
sudo systemctl restart nginx
```

### 5. Test

- Web: http://events.tugrul.app
- Health: http://events.tugrul.app/health
- Telegram: Find your bot

## What Happens at 02:00 Daily

1. ✅ Cron job triggers `/var/www/events/run_scraper.sh`
2. ✅ Scraper runs: `python3 scraper-script.py`
3. ✅ Scrapes Biletinial & BUBilet for Antalya events
4. ✅ Saves/updates events in MongoDB
5. ✅ Backend restarts automatically (refreshes RAG embeddings)
6. ✅ New events available in both web and Telegram

## Access Points

### Web Interface
- **URL**: http://events.tugrul.app
- **Chat API**: POST http://events.tugrul.app/api/chat
- **Events API**: GET http://events.tugrul.app/api/events

### Telegram Bot
- Find your bot on Telegram
- Send `/start` to begin
- Uses same RAG system as web

## Monitoring

```bash
# Check services
sudo systemctl status events
sudo systemctl status nginx

# View logs
sudo journalctl -u events -f
sudo tail -f /var/log/events/scraper.log

# Check bot usage
bash check-bot-usage.sh
```

## Everything is Ready! 🚀

All files are prepared and ready for deployment to your server at 65.21.182.26.

