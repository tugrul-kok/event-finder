from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
from threading import Thread
import logging

load_dotenv()

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)
CORS(app)

# MongoDB bağlantısı
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.server_info()
    db = client['events_db']
    events_collection = db['events']
    
    # Index oluştur
    try:
        events_collection.create_index([("city", 1), ("date", 1), ("category", 1)])
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")
    
    logger.info("✅ MongoDB connected successfully")
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    logger.error("Please make sure MongoDB is running or update MONGO_URI in .env")
    logger.error("For local MongoDB: brew services start mongodb-community")
    logger.error("Or use MongoDB Atlas and update MONGO_URI in .env")
    # Create dummy objects to prevent crashes
    db = None
    events_collection = None

# JSON serialization için helper
from flask.json.provider import DefaultJSONProvider

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json = CustomJSONProvider(app)

# MongoDB connection check helper
def check_mongodb():
    """Check if MongoDB is connected"""
    if events_collection is None:
        return False, jsonify({"success": False, "error": "MongoDB not connected. Please check your MongoDB connection."}), 503
    return True, None, None

# ============ FLASK API ENDPOINTS ============

# Chat API endpoint for web interface (MUST be before catch-all route)
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat_api():
    """Chat API endpoint for web interface - uses same RAG system as Telegram"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400
            
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"success": False, "error": "Message is required"}), 400
        
        logger.info(f"Web chat API - message: {user_message}")
        
        # Use the same RAG engine as Telegram bot
        rag_engine = get_rag_engine()
        
        if rag_engine:
            try:
                result = rag_engine.answer_question(
                    query=user_message,
                    city_filter='antalya',
                    top_k=5
                )
                answer = result.get('answer', '')
                if answer:
                    response = jsonify({"success": True, "answer": answer})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
            except Exception as e:
                logger.error(f"RAG engine error in web API: {e}")
                # Fallback to simple search
                pass
        
        # Fallback: Simple search
        params = parse_message(user_message)
        events = search_events(params)
        response_text = format_events_message(events, params)
        
        response = jsonify({"success": True, "answer": response_text})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        response = jsonify({"success": False, "error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# Web interface routes (AFTER API routes)
@app.route('/')
def index():
    """Serve web interface"""
    import os
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    if os.path.exists(web_dir):
        return send_from_directory(web_dir, 'index.html')
    else:
        return jsonify({"message": "Web interface not found. API is running.", "endpoints": ["/api/chat", "/api/events", "/health"]}), 200

@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    """Serve static files from web directory (only GET, excludes /api paths)"""
    import os
    # Don't serve API paths as static files
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    if os.path.exists(web_dir) and os.path.exists(os.path.join(web_dir, path)):
        return send_from_directory(web_dir, path)
    else:
        return jsonify({"error": "Not found"}), 404

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        if events_collection is None:
            return jsonify({"success": False, "error": "MongoDB not connected"}), 503
        
        city = request.args.get('city', '').lower()
        category = request.args.get('category', 'all').lower()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 50))
        
        query = {}
        if city and city != 'all':
            query['city'] = city
        if category and category != 'all':
            query['category'] = category
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query['$gte'] = start_date
            if end_date:
                date_query['$lte'] = end_date
            if date_query:
                query['date'] = date_query
        
        events = list(events_collection.find(query).sort('date', 1).limit(limit))
        
        for event in events:
            event['_id'] = str(event['_id'])
        
        return jsonify({"success": True, "count": len(events), "events": events})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/events', methods=['POST'])
def create_event():
    try:
        is_connected, error_response, status_code = check_mongodb()
        if not is_connected:
            return error_response, status_code
        
        data = request.get_json()
        required_fields = ['title', 'city', 'date', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
        
        event = {
            'title': data['title'],
            'description': data.get('description', ''),
            'city': data['city'].lower(),
            'category': data['category'].lower(),
            'date': data['date'],
            'time': data.get('time', ''),
            'venue': data.get('venue', ''),
            'address': data.get('address', ''),
            'price': data.get('price', 'Ücretsiz'),
            'url': data.get('url', ''),
            'image_url': data.get('image_url', ''),
            'organizer': data.get('organizer', ''),
            'tags': data.get('tags', []),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = events_collection.insert_one(event)
        event['_id'] = str(result.inserted_id)
        
        return jsonify({"success": True, "event": event}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/events/<event_id>', methods=['GET'])
def get_event(event_id):
    try:
        is_connected, error_response, status_code = check_mongodb()
        if not is_connected:
            return error_response, status_code
        
        event = events_collection.find_one({'_id': ObjectId(event_id)})
        if not event:
            return jsonify({"success": False, "error": "Event not found"}), 404
        event['_id'] = str(event['_id'])
        return jsonify({"success": True, "event": event})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    try:
        is_connected, error_response, status_code = check_mongodb()
        if not is_connected:
            return error_response, status_code
        
        data = request.get_json()
        data['updated_at'] = datetime.now()
        result = events_collection.update_one({'_id': ObjectId(event_id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({"success": False, "error": "Event not found"}), 404
        return jsonify({"success": True, "message": "Event updated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        is_connected, error_response, status_code = check_mongodb()
        if not is_connected:
            return error_response, status_code
        
        result = events_collection.delete_one({'_id': ObjectId(event_id)})
        if result.deleted_count == 0:
            return jsonify({"success": False, "error": "Event not found"}), 404
        return jsonify({"success": True, "message": "Event deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cities', methods=['GET'])
def get_cities():
    try:
        is_connected, error_response, status_code = check_mongodb()
        if not is_connected:
            return error_response, status_code
        
        cities = events_collection.distinct('city')
        return jsonify({"success": True, "cities": cities})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        is_connected, error_response, status_code = check_mongodb()
        if not is_connected:
            return error_response, status_code
        
        categories = events_collection.distinct('category')
        return jsonify({"success": True, "categories": categories})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/seed', methods=['POST'])
def seed_database():
    try:
        is_connected, error_response, status_code = check_mongodb()
        if not is_connected:
            return error_response, status_code
        
        events_collection.delete_many({})
        sample_events = [
            {
                'title': 'Rock Konseri - Duman',
                'description': 'Duman\'ın muhteşem konseri',
                'city': 'istanbul',
                'category': 'music',
                'date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
                'time': '20:00',
                'venue': 'Zorlu PSM',
                'address': 'Zorlu Center, Beşiktaş',
                'price': '250 TL - 500 TL',
                'url': 'https://example.com/duman',
                'organizer': 'Biletix',
                'tags': ['rock', 'konser', 'müzik'],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'title': 'Tiyatro: Hamlet',
                'description': 'Shakespeare\'in ölümsüz eseri',
                'city': 'istanbul',
                'category': 'theater',
                'date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                'time': '19:30',
                'venue': 'İstanbul Devlet Tiyatrosu',
                'address': 'Harbiye',
                'price': '100 TL',
                'url': 'https://example.com/hamlet',
                'organizer': 'Devlet Tiyatroları',
                'tags': ['tiyatro', 'klasik'],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'title': 'Modern Sanat Sergisi',
                'description': 'Çağdaş sanat eserleri',
                'city': 'ankara',
                'category': 'exhibition',
                'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '10:00',
                'venue': 'CerModern',
                'address': 'Altınsoy Caddesi',
                'price': 'Ücretsiz',
                'url': 'https://example.com/sergi',
                'organizer': 'CerModern',
                'tags': ['sergi', 'sanat'],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'title': 'Yazılım Workshop: Python ile AI',
                'description': 'Yapay zeka ve makine öğrenimi workshop\'u',
                'city': 'izmir',
                'category': 'workshop',
                'date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'time': '14:00',
                'venue': 'İzmir Ekonomi Üniversitesi',
                'address': 'Balçova',
                'price': '150 TL',
                'url': 'https://example.com/python-workshop',
                'organizer': 'Tech Academy',
                'tags': ['workshop', 'yazılım', 'python', 'ai'],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'title': 'Basketbol Maçı: Fenerbahçe - Galatasaray',
                'description': 'Derbi heyecanı',
                'city': 'istanbul',
                'category': 'sports',
                'date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                'time': '18:00',
                'venue': 'Ülker Sports Arena',
                'address': 'Ataşehir',
                'price': '200 TL - 800 TL',
                'url': 'https://example.com/derbi',
                'organizer': 'TBF',
                'tags': ['basketbol', 'spor', 'derbi'],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        ]
        events_collection.insert_many(sample_events)
        return jsonify({"success": True, "message": f"{len(sample_events)} events created"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ TELEGRAM BOT FUNCTIONS ============

def parse_turkish_date_query(query_text):
    """
    Kullanıcının Türkçe sorgusundan tarih aralığı çıkar (orijinal projeden).
    Örnekler:
    - "19 ekim" -> ("2025-10-19", "2025-10-19")
    - "bu hafta sonu" -> (cumartesi, pazar tarihleri)
    - "önümüzdeki 7 gün" -> (bugün, 7 gün sonrası)
    - "kasım ayı" -> ("2025-11-01", "2025-11-30")
    
    Returns: (başlangıç_tarihi, bitiş_tarihi) tuple (ISO format) veya (None, None)
    """
    import re
    
    text = query_text.lower().strip()
    today = datetime.now()
    
    month_to_num = {
        'ocak': 1, 'şubat': 2, 'subat': 2, 'mart': 3, 'nisan': 4,
        'mayıs': 5, 'mayis': 5, 'haziran': 6, 'temmuz': 7,
        'ağustos': 8, 'agustos': 8, 'eylül': 9, 'eylul': 9,
        'ekim': 10, 'kasım': 11, 'kasim': 11, 'aralık': 12, 'aralik': 12,
    }
    
    # 1. Belirli gün formatı: "19 ekim"
    pattern = r"(\d{1,2})\s+(ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik)"
    match = re.search(pattern, text)
    if match:
        try:
            day = int(match.group(1))
            month = month_to_num.get(match.group(2))
            if month and 1 <= day <= 31:
                year = today.year
                dt = datetime(year, month, day)
                # Geçmiş tarihse bir sonraki yıla al
                if dt < today:
                    dt = datetime(year + 1, month, day)
                date_str = dt.strftime('%Y-%m-%d')
                return (date_str, date_str)
        except ValueError:
            pass
    
    # 2. Ay bazlı sorgular: "kasım ayı", "kasımda"
    for month_name, month_num in month_to_num.items():
        if month_name in text:
            year = today.year
            if month_num < today.month:
                year += 1  # Geçmiş ay ise gelecek yıl olarak al
            start = datetime(year, month_num, 1)
            # Ayın son gününü hesapla
            if month_num == 12:
                end = datetime(year, 12, 31)
            else:
                end = datetime(year, month_num + 1, 1) - timedelta(days=1)
            return (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    
    # 3. Hafta sonu sorguları: "bu hafta sonu", "haftasonu"
    if 'bu hafta sonu' in text or 'haftasonu' in text:
        # Cumartesi gününe kadar olan gün sayısını hesapla
        days_until_saturday = (5 - today.weekday()) % 7
        saturday = today + timedelta(days=days_until_saturday)
        sunday = saturday + timedelta(days=1)
        return (saturday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d'))
    
    # 4. Günlük ve haftalık sorgular: "bugün", "yarın", "bu hafta"
    if 'bugün' in text or 'bugun' in text:
        return (today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    
    if 'yarın' in text or 'yarin' in text:
        tomorrow = today + timedelta(days=1)
        return (tomorrow.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d'))
    
    if 'bu hafta' in text:
        end_of_week = today + timedelta(days=(6 - today.weekday()))
        return (today.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d'))
    
    # 5. Gün sayısı bazlı: "önümüzdeki X gün", "gelecek 7 gün"
    match = re.search(r'(?:önümüzdeki|onumdeki|gelecek)\s+(\d+)\s+gün', text)
    if match:
        days = int(match.group(1))
        end_date = today + timedelta(days=days)
        return (today.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    return (None, None)

def parse_message(text):
    """Kullanıcının mesajını analiz eder - Sadece Antalya için"""
    text_lower = text.lower()
    
    # Şehir her zaman Antalya (proje sadece Antalya için)
    city = 'antalya'
    
    # Kategori tespiti
    categories = {
        'konser': 'music', 'müzik': 'music', 'concert': 'music',
        'tiyatro': 'theater', 'oyun': 'theater', 'theater': 'theater',
        'sergi': 'exhibition', 'galeri': 'exhibition', 'müze': 'exhibition',
        'workshop': 'workshop', 'atölye': 'workshop', 'eğitim': 'workshop', 'seminer': 'workshop',
        'spor': 'sports', 'maç': 'sports', 'futbol': 'sports', 'basketbol': 'sports',
        'sinema': 'cinema', 'film': 'cinema', 'movie': 'cinema'
    }
    category = 'all'
    for key, value in categories.items():
        if key in text_lower:
            category = value
            break
    
    # Tarih tespiti - Orijinal projenin parse_turkish_date_query fonksiyonunu kullan
    start_date, end_date = parse_turkish_date_query(text)
    
    # Eğer tarih bulunamazsa, varsayılan olarak bugünden 30 gün sonrasına kadar
    today = datetime.now()
    if not start_date:
        start_date = today.strftime('%Y-%m-%d')
    if not end_date:
        end_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
    
    return {
        'city': city,
        'category': category,
        'start_date': start_date,
        'end_date': end_date
    }

def search_events(params):
    """Veritabanından etkinlik arar - Sadece Antalya için"""
    if events_collection is None:
        logger.warning("MongoDB not connected - cannot search events")
        return []
    
    # Her zaman Antalya için ara
    query = {'city': 'antalya'}
    
    if params['category'] != 'all':
        query['category'] = params['category']
    
    # Tarih aralığı
    query['date'] = {'$gte': params['start_date'], '$lte': params['end_date']}
    
    # Debug logging
    logger.info(f"Search query: {query}")
    
    events = list(events_collection.find(query).sort('date', 1).limit(20))
    logger.info(f"Found {len(events)} events matching query")
    
    return events

def format_events_message(events, params):
    """Etkinlikleri Telegram mesajı formatına çevirir"""
    if not events:
        return f"😔 Üzgünüm, Antalya için belirttiğin kriterlerde etkinlik bulamadım.\n\n" \
               f"💡 Farklı bir tarih veya kategori dene!\n\n" \
               f"📝 Örnek: \"Bu hafta sonu konser var mı?\" veya \"Kasım ayı etkinlikleri\""
    
    emojis = {'music': '🎵', 'theater': '🎭', 'exhibition': '🖼️', 
              'workshop': '🛠️', 'sports': '⚽', 'cinema': '🎬'}
    
    message = f"🎉 {len(events)} etkinlik buldum:\n\n"
    message += "─────────────────────\n\n"
    
    for i, event in enumerate(events, 1):
        emoji = emojis.get(event.get('category', ''), '🎪')
        message += f"{emoji} *{i}. {event['title']}*\n"
        
        if event.get('date'):
            date_obj = datetime.strptime(event['date'], '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d %B %Y, %A')
            message += f"   📅 {formatted_date}"
            if event.get('time'):
                message += f" - {event['time']}"
            message += "\n"
        
        if event.get('venue'):
            message += f"   📍 {event['venue']}\n"
        if event.get('price'):
            message += f"   💰 {event['price']}\n"
        if event.get('url'):
            message += f"   🔗 [Detaylar]({event['url']})\n"
        
        message += "\n"
    
    message += "─────────────────────\n"
    message += "💡 Başka ne aramak istersin?"
    
    return message

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başladığında gönderilen mesaj"""
    user = update.effective_user
    user_name = user.first_name if user else "Kullanıcı"
    user_id = user.id if user else "Unknown"
    username = user.username if user and user.username else "No username"
    
    logger.info(f"User {user_name} (ID: {user_id}, @{username}) used /start command")
    
    welcome_message = f"Merhaba {user_name}! 🎉\n\n" \
                     f"Ben Antalya Etkinlik Botu. Antalya'da olan etkinlikleri bulmanıza yardımcı olabilirim.\n\n" \
                     f"📝 *Örnek sorular:*\n" \
                     f"• \"Bu hafta sonu konser var mı?\"\n" \
                     f"• \"Bugün tiyatro\"\n" \
                     f"• \"Yarın sinema\"\n" \
                     f"• \"Kasım ayı etkinlikleri\"\n" \
                     f"• \"19 ekim konser\"\n\n" \
                     f"🏙️ *Şehir:*\n" \
                     f"Antalya (sadece Antalya etkinlikleri)\n\n" \
                     f"🎭 *Kategoriler:*\n" \
                     f"Konser, Tiyatro, Sergi, Workshop, Spor, Sinema\n\n" \
                     f"📅 *Tarih örnekleri:*\n" \
                     f"Bugün, Yarın, Bu hafta sonu, Bu hafta, Kasım ayı, 19 ekim\n\n" \
                     f"Hadi başlayalım! Ne aramak istersin?"
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yardım komutu"""
    user = update.effective_user
    user_name = user.first_name if user else "Unknown"
    user_id = user.id if user else "Unknown"
    username = user.username if user and user.username else "No username"
    
    logger.info(f"User {user_name} (ID: {user_id}, @{username}) used /help command")
    
    help_text = "🤖 *Nasıl kullanılır?*\n\n" \
                "Bana doğal dilde mesaj at, ben seni anlayacağım!\n\n" \
                "📝 *Örnekler:*\n" \
                "• Bu hafta sonu konser\n" \
                "• Bugün tiyatro\n" \
                "• Yarın sinema var mı?\n" \
                "• Kasım ayı etkinlikleri\n" \
                "• 19 ekim konser\n\n" \
                "🏙️ *Şehir:* Antalya (sadece Antalya etkinlikleri)\n" \
                "🎭 *Kategoriler:* Konser, Tiyatro, Sergi, Workshop, Spor, Sinema\n" \
                "📅 *Tarihler:* Bugün, Yarın, Bu hafta sonu, Bu hafta, Kasım ayı, 19 ekim"
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# RAG Engine (lazy initialization)
_rag_engine = None
_rag_events_cache = None

def get_rag_engine():
    """Get or create RAG engine instance (lazy loading)"""
    global _rag_engine, _rag_events_cache
    
    if events_collection is None:
        return None
    
    # Check if we need to rebuild (events changed or first time)
    current_count = events_collection.count_documents({})
    
    if _rag_engine is None or _rag_events_cache != current_count:
        try:
            # Get all Antalya events from database
            all_events = list(events_collection.find({'city': 'antalya'}))
            
            if not all_events:
                logger.warning("No events found for RAG engine")
                return None
            
            logger.info(f"🔄 Initializing RAG engine with {len(all_events)} events...")
            from rag_engine import RAGEngine
            _rag_engine = RAGEngine(all_events)
            _rag_events_cache = current_count
            logger.info("✅ RAG engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    return _rag_engine

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcı mesajlarını işler - RAG sistemi kullanır"""
    try:
        user_message = update.message.text
        user = update.effective_user
        user_name = user.first_name if user else "Unknown"
        user_id = user.id if user else "Unknown"
        username = user.username if user and user.username else "No username"
        
        logger.info(f"User {user_name} (ID: {user_id}, @{username}) message: {user_message}")
        
        # Try RAG engine first (semantic search with embeddings)
        rag_engine = get_rag_engine()
        
        if rag_engine:
            try:
                # Use RAG for semantic search and AI-generated response
                result = rag_engine.answer_question(
                    query=user_message,
                    city_filter='antalya',
                    top_k=5
                )
                
                answer = result.get('answer', '')
                sources = result.get('sources', [])
                
                if answer:
                    # Send AI-generated response
                    await update.message.reply_text(
                        answer, 
                        parse_mode='Markdown', 
                        disable_web_page_preview=False  # Enable preview for links
                    )
                    logger.info(f"RAG response sent - {len(sources)} events used")
                    return
            except Exception as e:
                logger.error(f"RAG engine error: {e}")
                # Fallback to simple search
                pass
        
        # Fallback: Simple search (if RAG fails or not available)
        logger.info("Using fallback simple search")
        params = parse_message(user_message)
        logger.info(f"Parsed message '{user_message}' -> params: {params}")
        
        events = search_events(params)
        response = format_events_message(events, params)
        
        await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=True)
        logger.info(f"Simple search response sent - Found {len(events)} events")
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "⚠️ Üzgünüm, bir hata oluştu. Lütfen tekrar dener misin?",
            parse_mode='Markdown'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hata yakalayıcı"""
    logger.error(f"Update {update} caused error {context.error}")

async def run_telegram_bot_async():
    """Telegram botunu async olarak çalıştır"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    # Bot uygulaması oluştur
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Komutları ekle
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Botu başlat
    logger.info("Telegram bot starting...")
    try:
        async with application:
            await application.start()
            await application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES, 
                drop_pending_updates=True
            )
            logger.info("✅ Telegram bot is running and polling for updates...")
            
            # Keep running - updater will handle polling
            # Use a simple wait mechanism that can be interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Telegram bot stopping...")
                await application.updater.stop()
                await application.stop()
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
        import traceback
        logger.error(traceback.format_exc())

def run_telegram_bot():
    """Telegram botunu ayrı thread'de çalıştır"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    # Python 3.12+ için yeni event loop oluştur (thread için)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(run_telegram_bot_async())
    except KeyboardInterrupt:
        logger.info("Telegram bot stopped by user")
    except Exception as e:
        logger.error(f"Telegram bot thread error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        try:
            # Cancel all tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            # Wait for cancellation
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
        except:
            pass

# Flask ve Telegram bot'u birlikte çalıştır
def start_flask():
    """Flask uygulamasını başlat"""
    port = int(os.getenv('API_PORT', 5001))  # Changed default to 5001 (5000 is used by AirPlay on macOS)
    host = os.getenv('API_HOST', '127.0.0.1')
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    # Try to use the port, if it fails, try next port
    import socket
    for attempt in range(5):
        test_port = port + attempt
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, test_port))
        sock.close()
        if result != 0:  # Port is available
            if attempt > 0:
                logger.info(f"Port {port} was in use, using port {test_port} instead")
            port = test_port
            break
    else:
        logger.warning(f"Could not find available port starting from {port}")
    
    logger.info(f"🌐 Starting Flask API on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False)

if __name__ == '__main__':
    # Telegram bot'u ayrı thread'de çalıştır
    bot_thread = Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Flask API'yi ana thread'de çalıştır
    logger.info("Starting Flask API...")
    start_flask()