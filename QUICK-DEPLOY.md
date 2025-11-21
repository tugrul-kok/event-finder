# 🚀 Quick Deployment Guide

## Server Info
- **IP**: 65.21.182.26
- **Domain**: events.tugrul.app
- **Web**: http://events.tugrul.app
- **API**: http://events.tugrul.app/api

## Quick Steps

### 1. Upload Files to Server

```bash
# Option A: Using SCP
cd /Users/tugrul/Desktop/amean/events
scp -r * root@65.21.182.26:/tmp/events-deploy/

# Option B: Using Git (recommended)
# On server:
cd /tmp
git clone <your-repo-url> events-deploy
```

### 2. Run Deployment

```bash
# SSH to server
ssh root@65.21.182.26

# Run deployment
cd /tmp/events-deploy
chmod +x deploy-script.sh
sudo ./deploy-script.sh
```

### 3. Configure .env

```bash
nano /var/www/events/.env
```

Add:
```bash
MONGO_URI=mongodb://localhost:27017/
FLASK_ENV=production
SECRET_KEY=your-secret-key
API_PORT=5001
API_HOST=127.0.0.1
TELEGRAM_BOT_TOKEN=your-token
GEMINI_API_KEY=your-key
```

### 4. Restart Services

```bash
sudo systemctl restart events
sudo systemctl restart nginx
```

### 5. Test

- Web: http://events.tugrul.app
- Health: http://events.tugrul.app/health
- Telegram: Find your bot and send `/start`

## Auto-Scraping

✅ Already configured! Runs daily at 02:00
- Scrapes events from Biletinial & BUBilet
- Saves to MongoDB
- Refreshes RAG embeddings (by restarting backend)

## What's Included

✅ Web interface at events.tugrul.app
✅ Telegram bot (same backend)
✅ RAG system (embeddings + Gemini)
✅ Auto-scraping at 02:00 daily
✅ Nginx reverse proxy
✅ Systemd service
✅ Cron job

## Check Status

```bash
sudo systemctl status events
sudo systemctl status nginx
curl http://events.tugrul.app/health
```

