# 🚀 Server Deployment Guide

## Server Information
- **IP Address**: 65.21.182.26
- **Domain**: events.tugrul.app
- **Web Interface**: http://events.tugrul.app
- **API**: http://events.tugrul.app/api

## Features
- ✅ **Web Interface**: Chat interface at events.tugrul.app
- ✅ **Telegram Bot**: Same backend, works via Telegram
- ✅ **RAG System**: Semantic search with embeddings
- ✅ **Auto Scraping**: Daily at 02:00 (scraping + embeddings refresh)

## Pre-Deployment Checklist

### 1. Domain Setup
Make sure `events.tugrul.app` DNS points to `65.21.182.26`:
```bash
# Check DNS
dig events.tugrul.app
# Should return: 65.21.182.26
```

### 2. Server Requirements
- Ubuntu/Debian server
- Root or sudo access
- Port 80 open (for HTTP)
- Port 443 open (for HTTPS - optional)

### 3. Prepare Files
On your local machine, make sure you have:
- All project files
- `.env` file with your API keys (will be copied to server)

## Deployment Steps

### Step 1: Upload Files to Server

```bash
# From your local machine
cd /Users/tugrul/Desktop/amean/events

# Upload to server (replace with your server details)
scp -r * root@65.21.182.26:/tmp/events-deploy/
```

Or use git:
```bash
# On server
cd /tmp
git clone <your-repo-url> events-deploy
cd events-deploy
```

### Step 2: Run Deployment Script

```bash
# On server
cd /tmp/events-deploy
chmod +x deploy-script.sh
sudo ./deploy-script.sh
```

The script will:
- Install system packages (Python, MongoDB, Nginx)
- Create project directory at `/var/www/events`
- Set up virtual environment
- Install Python dependencies
- Configure Nginx for events.tugrul.app
- Set up systemd service
- Configure cron job (02:00 daily scraping)
- Start services

### Step 3: Configure Environment Variables

```bash
# On server
nano /var/www/events/.env
```

Add your API keys:
```bash
MONGO_URI=mongodb://localhost:27017/
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
API_PORT=5001
API_HOST=127.0.0.1

# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Gemini API Key
GEMINI_API_KEY=your-gemini-api-key
```

### Step 4: Restart Services

```bash
sudo systemctl restart events
sudo systemctl restart nginx
```

### Step 5: Verify Deployment

```bash
# Check services
sudo systemctl status events
sudo systemctl status nginx

# Test web interface
curl http://events.tugrul.app/health

# Check logs
sudo journalctl -u events -f
```

## Daily Auto-Scraping (02:00)

The cron job is automatically set up to:
1. Run scraper at 02:00 every day
2. Scrape events from Biletinial and BUBilet
3. Save to MongoDB
4. RAG embeddings will be rebuilt when backend restarts or on first query

To manually trigger scraping:
```bash
sudo -u www-data /var/www/events/run_scraper.sh
```

## Access Points

### Web Interface
- **URL**: http://events.tugrul.app
- **Features**: Chat interface, same RAG system as Telegram

### Telegram Bot
- **Usage**: Find your bot on Telegram, send `/start`
- **Same Backend**: Uses same RAG engine and database

### API Endpoints
- **Health**: http://events.tugrul.app/health
- **Chat API**: POST http://events.tugrul.app/api/chat
- **Events API**: GET http://events.tugrul.app/api/events

## Monitoring

### Check Bot Usage
```bash
bash check-bot-usage.sh
```

### View Logs
```bash
# Backend logs
sudo journalctl -u events -f

# Scraper logs
sudo tail -f /var/log/events/scraper.log

# Cron logs
sudo tail -f /var/log/events/scraper_cron.log

# Nginx logs
sudo tail -f /var/log/nginx/events_access.log
```

### Check Database
```bash
mongosh mongodb://localhost:27017/events_db
db.events.countDocuments()
db.events.find({city: 'antalya'}).limit(5).pretty()
```

## SSL/HTTPS Setup (Optional but Recommended)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d events.tugrul.app

# Auto-renewal test
sudo certbot renew --dry-run
```

## Troubleshooting

### Service Not Starting
```bash
sudo systemctl status events
sudo journalctl -u events -n 50
```

### Nginx Not Working
```bash
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/events_error.log
```

### Scraper Not Running
```bash
# Check cron job
sudo crontab -u www-data -l

# Manual test
sudo -u www-data /var/www/events/run_scraper.sh
```

### RAG Not Working
- Check if embeddings are being created (first query takes longer)
- Check Gemini API key in `.env`
- Check logs for RAG errors

## File Structure on Server

```
/var/www/events/
├── app.py                    # Main backend (events_backend.py)
├── scraper-script.py         # Scraper
├── rag_engine.py             # RAG engine
├── rag_retriever.py          # FAISS retriever
├── requirements.txt          # Dependencies
├── .env                      # Environment variables
├── web/                      # Web interface
│   └── index.html
├── venv/                     # Virtual environment
└── run_scraper.sh           # Cron script

/etc/nginx/sites-available/
└── events                    # Nginx config

/etc/systemd/system/
└── events.service           # Systemd service

/var/log/events/
├── scraper.log              # Scraper logs
├── scraper_cron.log         # Cron logs
├── access.log               # API access logs
└── error.log                # API error logs
```

## Updates

To update the application:
```bash
# Pull latest code
cd /var/www/events
git pull  # or upload new files

# Restart service
sudo systemctl restart events
```

## Support

For issues, check:
1. Service logs: `sudo journalctl -u events -f`
2. Nginx logs: `sudo tail -f /var/log/nginx/events_error.log`
3. Scraper logs: `sudo tail -f /var/log/events/scraper.log`

