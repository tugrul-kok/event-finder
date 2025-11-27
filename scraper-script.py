"""
Real Event Scraper for Antalya
Based on working scrapers from the original rotiva project
Only supports Antalya city
"""

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime, timedelta
from urllib.parse import urljoin
import os
from dotenv import load_dotenv
import logging
import re
import time

# .env dosyasından environment variable'ları yükle
load_dotenv()

# Logging ayarları
import pathlib
log_dir = pathlib.Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(log_dir / 'scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MongoDB bağlantısı (.env'den okunur)
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

# Gemini API Key (.env dosyasından okunur)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.warning("⚠️  GEMINI_API_KEY .env dosyasında bulunamadı")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client['events_db']
    events_collection = db['events']
    logger.info("✅ MongoDB connected successfully")
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    raise

# Gemini AI yapılandırması (opsiyonel - kategorizasyon için)
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        # Try gemini-2.5-flash first, fallback to gemini-pro
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
        except:
            try:
                model = genai.GenerativeModel('gemini-pro')
            except:
                model = None
        if model:
            logger.info("✅ Gemini AI configured")
        else:
            logger.warning("Gemini model could not be initialized")
    except Exception as e:
        logger.warning(f"Gemini AI configuration failed: {e}")
        model = None
else:
    logger.warning("GEMINI_API_KEY bulunamadı, basit kategorizasyon kullanılacak")
    model = None

# ============ HELPER FUNCTIONS ============

def clean_text(text):
    """Metindeki fazla boşlukları temizle ve tek satıra indir"""
    if not text:
        return ''
    return ' '.join(str(text).split())

def parse_date_from_text(text: str):
    """Türkçe metinden YYYY-MM-DD formatında tarih çıkar. Bulamazsa None döner.
    Örnekler: '23 Ekim', '23 Ekim Per - 20:00', '02 Kasım Paz - 21:00'
    Not: Yıl belirtilmemişse mevcut yılı varsayar.
    """
    if not text:
        return None
    
    t = text.lower()
    # Türkçe ay isimleri ve karşılık gelen sayıları
    month_to_num = {
        'ocak': 1, 'şubat': 2, 'subat': 2, 'mart': 3, 'nisan': 4, 'mayıs': 5, 'mayis': 5,
        'haziran': 6, 'temmuz': 7, 'ağustos': 8, 'agustos': 8, 'eylül': 9, 'eylul': 9,
        'ekim': 10, 'kasım': 11, 'kasim': 11, 'aralık': 12, 'aralik': 12,
    }
    # Gün + Ay formatını bul (örnek: "23 ekim")
    m = re.search(r"\b(\d{1,2})\s+(ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik)\b", t)
    if not m:
        return None
    try:
        day = int(m.group(1))
        month = month_to_num.get(m.group(2))
        if not month:
            return None
        year = datetime.now().year
        dt = datetime(year, month, day)
        # Geçmiş tarihse bir sonraki yıla al
        if dt < datetime.now():
            dt = datetime(year + 1, month, day)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return None

def normalize_event_date(event_date_str):
    """
    Etkinlik tarihini ISO formatına (YYYY-MM-DD) çevir.
    Giriş örnekleri: "23 Ekim 2025", "23 Ekim", "23 Ekim Per - 20:00"
    Çıkış: "2025-10-23" veya None (başarısızsa)
    """
    if not event_date_str:
        return None
    
    text = str(event_date_str).lower().strip()
    
    month_to_num = {
        'ocak': 1, 'şubat': 2, 'subat': 2, 'mart': 3, 'nisan': 4, 
        'mayıs': 5, 'mayis': 5, 'haziran': 6, 'temmuz': 7, 
        'ağustos': 8, 'agustos': 8, 'eylül': 9, 'eylul': 9,
        'ekim': 10, 'kasım': 11, 'kasim': 11, 'aralık': 12, 'aralik': 12,
    }
    
    # Gün + Ay + (opsiyonel Yıl) formatını ara
    pattern = r"(\d{1,2})\s+(ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik)(?:\s+(\d{4}))?"
    match = re.search(pattern, text)
    
    if match:
        try:
            day = int(match.group(1))
            month = month_to_num.get(match.group(2))
            year = int(match.group(3)) if match.group(3) else datetime.now().year
            
            if month and 1 <= day <= 31:
                dt = datetime(year, month, day)
                # Geçmiş tarihse bir sonraki yıla al
                if dt < datetime.now():
                    dt = datetime(year + 1, month, day)
                return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    return None

def categorize_with_gemini(event_title, description=""):
    """Gemini AI ile etkinlik kategorisini belirler"""
    if not model:
        return categorize_simple(event_title)
    
    try:
        prompt = f"""
        Aşağıdaki etkinlik başlığını ve açıklamasını analiz et ve sadece TEK bir kategori döndür:
        
        Başlık: {event_title}
        Açıklama: {description[:200]}
        
        Kategori seçenekleri:
        - music (konser, müzik, band, DJ, festival)
        - theater (tiyatro, oyun, drama)
        - exhibition (sergi, galeri, müze)
        - workshop (workshop, atölye, eğitim, seminer)
        - sports (spor, maç, futbol, basketbol)
        - cinema (sinema, film)
        
        Sadece kategori adını döndür, başka bir şey yazma.
        """
        
        response = model.generate_content(prompt)
        category = response.text.strip().lower()
        
        valid_categories = ['music', 'theater', 'exhibition', 'workshop', 'sports', 'cinema']
        if category in valid_categories:
            return category
        else:
            return categorize_simple(event_title)
            
    except Exception as e:
        logger.error(f"Gemini API hatası: {e}")
        return categorize_simple(event_title)

def categorize_simple(event_title):
    """Basit keyword bazlı kategorizasyon (fallback)"""
    title_lower = str(event_title).lower()
    
    music_keywords = ['konser', 'müzik', 'concert', 'festival', 'band', 'dj', 'canlı müzik']
    theater_keywords = ['tiyatro', 'oyun', 'theater', 'sahne', 'drama']
    exhibition_keywords = ['sergi', 'exhibition', 'galeri', 'müze', 'sanat']
    workshop_keywords = ['workshop', 'atölye', 'eğitim', 'seminer', 'kurs']
    sports_keywords = ['maç', 'spor', 'futbol', 'basketbol', 'voleybol', 'sports']
    cinema_keywords = ['sinema', 'film', 'cinema', 'movie']
    
    if any(keyword in title_lower for keyword in music_keywords):
        return 'music'
    elif any(keyword in title_lower for keyword in theater_keywords):
        return 'theater'
    elif any(keyword in title_lower for keyword in exhibition_keywords):
        return 'exhibition'
    elif any(keyword in title_lower for keyword in workshop_keywords):
        return 'workshop'
    elif any(keyword in title_lower for keyword in sports_keywords):
        return 'sports'
    elif any(keyword in title_lower for keyword in cinema_keywords):
        return 'cinema'
    else:
        return 'music'  # Default

# ============ SCRAPERS ============

def scrape_biletinial():
    """Biletinial sitesinden Antalya etkinliklerini çeker"""
    logger.info("🔄 Biletinial scraping başladı (Antalya)...")
    events = []
    
    base_url = "https://biletinial.com"
    target_urls = {
        'antalya_sinema': 'https://biletinial.com/tr-tr/sinema/antalya',
        'antalya_events': 'https://biletinial.com/tr-tr/sehrineozel/antalya'
    }
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        for url_key, url in target_urls.items():
            logger.info(f"📡 {url_key} çekiliyor: {url}")
            
            try:
                response = session.get(url, timeout=20)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Farklı selektörleri dene
                selectors = [
                    "a[href*='/tiyatro/']",
                    "a[href*='/sinema/']",
                    "a[href*='/etkinlik/']",
                ]
                
                found_links = []
                for selector in selectors:
                    links = soup.select(selector)
                    if links:
                        found_links.extend(links)
                
                logger.info(f"   → {len(found_links)} etkinlik linki bulundu")
                
                seen_urls = set()
                
                for link in found_links[:30]:  # İlk 30 link
                    try:
                        event_data = {
                            'title': '',
                            'date': '',
                            'time': '',
                            'venue': '',
                            'address': '',
                            'city': 'antalya',
                            'price': '',
                            'description': '',
                            'url': '',
                            'source': 'Biletinial'
                        }
                        
                        # URL
                        href = link.get('href')
                        if href:
                            full_url = href if href.startswith('http') else urljoin(base_url, href)
                            event_data['url'] = full_url
                            if event_data['url'] in seen_urls:
                                continue
                            seen_urls.add(event_data['url'])
                        
                        # Başlık
                        event_data['title'] = clean_text(link.get_text(" ")) or clean_text(link.get('title', ''))
                        
                        if not event_data['title']:
                            title_selectors = ['h3', 'h4', 'h5', '.title', '[class*="title"]']
                            for sel in title_selectors:
                                title_el = link.select_one(sel)
                                if title_el:
                                    event_data['title'] = clean_text(title_el.get_text(" "))
                                    break
                        
                        # Gereksiz linkleri filtrele
                        if event_data['title'] and any(skip in event_data['title'].lower() for skip in ['tümünü', 'müşteri hizmet', 'keşfet']):
                            continue
                        
                        if event_data['title'] and len(event_data['title']) > 3 and event_data['url']:
                            events.append(event_data)
                            logger.info(f"   ✅ Etkinlik {len(events)}: {event_data['title'][:50]}...")
                    
                    except Exception as e:
                        logger.debug(f"Link işleme hatası: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"   ❌ {url_key} çekilemedi: {e}")
                continue
        
        logger.info(f"✅ Biletinial'ten {len(events)} etkinlik çekildi")
        
    except Exception as e:
        logger.error(f"❌ Biletinial scraping hatası: {e}")
    
    return events

def scrape_bubilet():
    """BUBilet sitesinden Antalya etkinliklerini çeker"""
    logger.info("🔄 BUBilet scraping başladı (Antalya)...")
    events = []
    
    base_url = "https://www.bubilet.com.tr"
    target_url = 'https://www.bubilet.com.tr/antalya'
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        logger.info(f"📡 Antalya çekiliyor: {target_url}")
        
        response = session.get(target_url, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Etkinlik linklerini bul
        event_links = soup.select("a[href*='/etkinlik/']")
        logger.info(f"   → {len(event_links)} etkinlik linki bulundu")
        
        seen_urls = set()
        
        for link in event_links:
            try:
                event_data = {
                    'title': '',
                    'date': '',
                    'time': '',
                    'venue': '',
                    'address': '',
                    'city': 'antalya',
                    'price': '',
                    'description': '',
                    'url': '',
                    'source': 'BUBilet'
                }
                
                # URL
                href = link.get('href')
                if href:
                    full_url = href if href.startswith('http') else urljoin(base_url, href)
                    event_data['url'] = full_url
                    if event_data['url'] in seen_urls:
                        continue
                    seen_urls.add(event_data['url'])
                
                # Başlık (h3)
                h3 = link.select_one("h3")
                if h3:
                    event_data['title'] = clean_text(h3.get_text(" "))
                
                # Title from attribute fallback
                if not event_data['title']:
                    title_attr = link.get('title')
                    if title_attr:
                        event_data['title'] = clean_text(title_attr)
                
                # Yer ve Tarih (p tags)
                p_tags = link.select("p.text-gray-500")
                if len(p_tags) >= 1:
                    event_data['venue'] = clean_text(p_tags[0].get_text(" "))
                if len(p_tags) >= 2:
                    date_text = clean_text(p_tags[1].get_text(" "))
                    # Parse tarih ISO formatına
                    parsed = parse_date_from_text(date_text)
                    if parsed:
                        event_data['date'] = parsed
                    else:
                        event_data['date'] = date_text
                
                # Fiyat (span.tracking-tight)
                price_span = link.select_one("span.tracking-tight")
                if price_span:
                    price_text = clean_text(price_span.get_text(" "))
                    if price_text and not price_text.endswith('₺'):
                        event_data['price'] = price_text + " ₺"
                    else:
                        event_data['price'] = price_text
                
                if event_data['title'] and len(event_data['title']) > 3 and event_data['url']:
                    events.append(event_data)
                    logger.info(f"   ✅ Etkinlik {len(events)}: {event_data['title'][:50]}...")
            
            except Exception as e:
                logger.debug(f"Link işleme hatası: {e}")
                continue
        
        logger.info(f"✅ BUBilet'ten {len(events)} etkinlik çekildi")
        
    except Exception as e:
        logger.error(f"❌ BUBilet scraping hatası: {e}")
    
    return events

def scrape_biletix():
    """Biletix sitesinden Antalya etkinliklerini çeker (Selenium ile dinamik içerik)"""
    logger.info("🔄 Biletix scraping başladı (Antalya)...")
    events = []
    
    base_url = "https://www.biletix.com"
    # Antalya için özel arama sayfası (örnek scraper'dan alındı)
    target_url = 'https://www.biletix.com/search/TURKIYE/tr?category_sb=-1&date_sb=-1&city_sb=Antalya#!city_sb:Antalya'
    
    # Selenium ile dinamik içerik yükleme
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
    except ImportError:
        logger.warning("⚠️  Selenium bulunamadı, Biletix scraping atlanıyor. 'pip install selenium webdriver-manager' ile yükleyin.")
        return events
    
    driver = None
    try:
        logger.info(f"📡 Biletix Antalya çekiliyor (Selenium ile): {target_url}")
        
        # Headless Chrome ayarları
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # ChromeDriver'ı otomatik yükle
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            logger.warning(f"⚠️  ChromeDriver yüklenemedi: {e}. Sistem ChromeDriver kullanılacak.")
            driver = webdriver.Chrome(options=chrome_options)
        
        # Sayfayı yükle
        logger.info(f"   → URL açılıyor: {target_url}")
        driver.get(target_url)
        
        # Sayfa yüklenmesini bekle
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            logger.warning("   ⚠️  Sayfa yüklenme timeout, devam ediliyor...")
        
        logger.info("   → Sayfa yüklendi, dinamik içerik bekleniyor...")
        time.sleep(15)  # Örnek scraper'da 15 saniye bekleniyor
        
        # Sayfa başlığını kontrol et
        page_title = driver.title
        logger.info(f"   → Sayfa başlığı: {page_title}")
        
        # URL'nin değişip değişmediğini kontrol et (redirect olabilir)
        current_url = driver.current_url
        if current_url != target_url:
            logger.info(f"   → URL redirect oldu: {current_url}")
            # Eğer 404'e yönlendirildiyse, farklı bir URL dene
            if '404' in current_url.lower():
                logger.warning("   ⚠️  404 hatası alındı, alternatif URL deneniyor...")
                # Alternatif URL'yi dene
                alt_url = 'https://www.biletix.com/anasayfa/ETKINLIK/tr'
                logger.info(f"   → Alternatif URL deneniyor: {alt_url}")
                driver.get(alt_url)
                time.sleep(15)
        
        # Sayfayı kademeli scroll et (lazy loading için) - örnek scraper'dan
        logger.info("   → Sayfa scroll ediliyor...")
        for i in range(5):  # Örnek scraper'da 5 kez scroll ediliyor
            driver.execute_script(f"window.scrollTo(0, {(i+1) * 800});")
            time.sleep(2)
        
        # Son scroll
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Örnek scraper'da 5 saniye bekleniyor
        
        # Etkinlik kartlarını bul - örnek scraper'dan alındı
        # Önce ana selector'ı dene: .flexibleEvent
        event_cards = driver.find_elements(By.CSS_SELECTOR, ".flexibleEvent")
        logger.info(f"   → .flexibleEvent ile {len(event_cards)} etkinlik kartı bulundu")
        
        # Eğer bulunamadıysa alternatif selector'ları dene
        if not event_cards:
            logger.warning("   ⚠️  .flexibleEvent ile kart bulunamadı, alternatif selector'lar deneniyor...")
            event_cards = driver.find_elements(By.CSS_SELECTOR, 
                ".searchResultEvent, .listevent, .event, .card, .item")
            logger.info(f"   → Alternatif selector'lar ile {len(event_cards)} etkinlik kartı bulundu")
        
        # Kartların içeriğini kontrol et (örnek scraper'dan)
        valid_cards = []
        for i, card in enumerate(event_cards):
            try:
                # Kartın içeriğini kontrol et
                card_html = card.get_attribute('innerHTML')
                if card_html and len(card_html.strip()) > 50:  # En az 50 karakter içerik
                    valid_cards.append(card)
                    logger.debug(f"   → Kart {i+1}: İçerik bulundu ({len(card_html)} karakter)")
                else:
                    logger.debug(f"   → Kart {i+1}: Boş içerik")
            except Exception as e:
                logger.debug(f"   → Kart {i+1}: Kontrol hatası - {e}")
        
        logger.info(f"   → İçerikli kart sayısı: {len(valid_cards)}")
        event_cards = valid_cards  # Sadece içerikli kartları kullan
        
        # Eğer hala bulunamadıysa, link bazlı arama yap
        if not event_cards:
            logger.warning("   ⚠️  Etkinlik kartı bulunamadı, sayfa yapısı analiz ediliyor...")
            
            # Sayfa kaynağını kontrol et
            page_source = driver.page_source
            logger.debug(f"   → Sayfa kaynağı uzunluğu: {len(page_source)} karakter")
            
            # Tüm linkleri kontrol et
            all_links = driver.find_elements(By.TAG_NAME, "a")
            logger.info(f"   → Sayfada toplam {len(all_links)} link bulundu")
            
            event_cards = []
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href:
                        # Biletix URL pattern'lerini kontrol et
                        if any(pattern in href.lower() for pattern in ['/etkinlik/', '/event/', 'biletix.com/anasayfa/', 'biletix.com/search']):
                            # Ana sayfa ve arama sayfalarını filtrele
                            if '/anasayfa/' not in href and '/search' not in href:
                                event_cards.append(link)
                except:
                    continue
            
            logger.info(f"   → Link bazlı arama ile {len(event_cards)} potansiyel etkinlik bulundu")
            
            # Eğer hala bulunamadıysa, sayfanın body içeriğini kontrol et
            if not event_cards:
                try:
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    logger.debug(f"   → Body metni uzunluğu: {len(body_text)} karakter")
                    if len(body_text) < 100:
                        logger.warning("   ⚠️  Sayfa içeriği çok kısa, muhtemelen yüklenmedi veya hata var")
                except:
                    pass
        
        seen_urls = set()
        
        for i, card in enumerate(event_cards[:20]):  # İlk 20 geçerli etkinliği al (örnek scraper'dan)
            try:
                logger.info(f"   → Etkinlik {i+1} çıkarılıyor...")
                
                # Önce kartın tüm metnini al (örnek scraper'dan)
                all_text = clean_text(card.text)
                logger.debug(f"      → Kart metni: {all_text[:100]}...")
                
                event_data = {
                    'title': '',
                    'date': '',
                    'time': '',
                    'venue': '',
                    'address': '',
                    'city': 'antalya',
                    'price': '',
                    'description': '',
                    'url': '',
                    'source': 'Biletix'
                }
                
                # URL bul (örnek scraper'dan)
                try:
                    link_elem = card.find_element(By.TAG_NAME, 'a')
                    href = link_elem.get_attribute('href')
                    if href:
                        event_data['url'] = href if href.startswith('http') else urljoin(base_url, href)
                        if event_data['url'] in seen_urls:
                            logger.debug(f"      → Duplicate URL, atlanıyor: {event_data['url']}")
                            continue
                        seen_urls.add(event_data['url'])
                        logger.debug(f"      → URL bulundu: {event_data['url']}")
                except NoSuchElementException:
                    logger.debug(f"      → Link bulunamadı")
                    pass
                
                # Başlık bul - örnek scraper'dan (daha geniş selector'lar)
                title_selectors = [
                    '.event-title', '.title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    '[data-testid*="title"]', '.event-name', '.name', '.heading',
                    'a[href*="/etkinlik/"]', 'a[href*="/event/"]'
                ]
                
                for selector in title_selectors:
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, selector)
                        title_text = clean_text(title_elem.text)
                        if title_text and len(title_text) > 3:
                            event_data['title'] = title_text
                            logger.debug(f"      → Başlık bulundu: {title_text[:50]}...")
                            break
                    except NoSuchElementException:
                        continue
                
                # Eğer başlık bulunamazsa, link metnini kullan (örnek scraper'dan)
                if not event_data['title']:
                    try:
                        link_elem = card.find_element(By.TAG_NAME, 'a')
                        link_text = clean_text(link_elem.text)
                        if link_text and len(link_text) > 3:
                            event_data['title'] = link_text
                            logger.debug(f"      → Link metni başlık olarak kullanıldı: {link_text[:50]}...")
                    except NoSuchElementException:
                        pass
                
                # Tarih bul - örnek scraper'dan
                date_selectors = [
                    '.event-date', '.date', '.event-time', '.time', '.datetime',
                    '[data-testid*="date"]', '.tarih', '.tarih-saat'
                ]
                
                for selector in date_selectors:
                    try:
                        date_elem = card.find_element(By.CSS_SELECTOR, selector)
                        date_text = clean_text(date_elem.text)
                        if date_text:
                            # Parse tarih ISO formatına
                            parsed = parse_date_from_text(date_text)
                            if parsed:
                                event_data['date'] = parsed
                            else:
                                event_data['date'] = date_text
                            logger.debug(f"      → Tarih bulundu: {date_text}")
                            break
                    except NoSuchElementException:
                        continue
                
                # Konum/Venue bul - örnek scraper'dan
                location_selectors = [
                    '.event-location', '.location', '.venue', '.place', '.mekan',
                    '[data-testid*="location"]', '.adres', '.yer'
                ]
                
                for selector in location_selectors:
                    try:
                        location_elem = card.find_element(By.CSS_SELECTOR, selector)
                        location_text = clean_text(location_elem.text)
                        if location_text:
                            event_data['venue'] = location_text
                            logger.debug(f"      → Konum bulundu: {location_text}")
                            break
                    except NoSuchElementException:
                        continue
                
                # Fiyat bul - örnek scraper'dan
                price_selectors = [
                    '.event-price', '.price', '.ticket-price', '.fiyat', '.cost',
                    '[data-testid*="price"]', '.amount', '.fee'
                ]
                
                for selector in price_selectors:
                    try:
                        price_elem = card.find_element(By.CSS_SELECTOR, selector)
                        price_text = clean_text(price_elem.text)
                        if price_text:
                            event_data['price'] = price_text
                            logger.debug(f"      → Fiyat bulundu: {price_text}")
                            break
                    except NoSuchElementException:
                        continue
                
                # Eğer hiçbir şey bulunamazsa, kartın tüm metnini analiz et (örnek scraper'dan)
                if not event_data['title'] and all_text:
                    # Basit metin analizi ile başlık çıkar
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    if lines:
                        # En uzun satırı başlık olarak kullan
                        event_data['title'] = max(lines, key=len)
                        logger.debug(f"      → Metin analizi ile başlık: {event_data['title'][:50]}...")
                
                # Gereksiz linkleri filtrele
                if event_data['title'] and any(skip in event_data['title'].lower() for skip in ['tümünü', 'müşteri hizmet', 'keşfet', 'daha fazla']):
                    logger.debug(f"      → Gereksiz link filtrelendi: {event_data['title']}")
                    continue
                
                # En az başlık varsa etkinliği kabul et (örnek scraper'dan)
                if event_data['title'] and len(event_data['title']) > 3:
                    events.append(event_data)
                    logger.info(f"   ✅ Etkinlik {len(events)}: {event_data['title'][:50]}...")
                else:
                    logger.debug(f"      → Etkinlik verisi çıkarılamadı (başlık yok veya çok kısa)")
            
            except Exception as e:
                logger.error(f"   ❌ Etkinlik {i+1} çıkarılırken hata: {e}")
                continue
        
        logger.info(f"✅ Biletix'ten {len(events)} etkinlik çekildi")
        
    except Exception as e:
        logger.error(f"❌ Biletix scraping hatası: {e}")
        import traceback
        logger.debug(traceback.format_exc())
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return events

# ============ PROCESS AND SAVE ============

def process_and_save_events(raw_events):
    """Etkinlikleri işler ve veritabanına kaydeder"""
    logger.info(f"📊 Toplam {len(raw_events)} etkinlik işleniyor...")
    
    saved_count = 0
    updated_count = 0
    
    for event in raw_events:
        try:
            # Tarih normalleştir
            date_str = event.get('date', '')
            if date_str:
                normalized_date = normalize_event_date(date_str)
                if normalized_date:
                    event['date'] = normalized_date
                elif not date_str.startswith('202'):  # Eğer zaten ISO formatında değilse
                    # Tarih parse edilemediyse, bugünden 7 gün sonrasını varsay
                    event['date'] = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            else:
                # Tarih yoksa, bugünden 7 gün sonrasını varsay
                event['date'] = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Kategori belirle
            category = categorize_with_gemini(event.get('title', ''), event.get('description', ''))
            
            # Etkinlik objesi oluştur
            event_data = {
                'title': event.get('title', '').strip(),
                'description': event.get('description', ''),
                'city': 'antalya',  # Sadece Antalya
                'category': category,
                'date': event['date'],
                'time': event.get('time', ''),
                'venue': event.get('venue', ''),
                'address': event.get('address', ''),
                'price': event.get('price', 'Bilet için tıklayın'),
                'url': event.get('url', ''),
                'image_url': event.get('image_url', ''),
                'organizer': event.get('source', 'Bilinmiyor'),
                'tags': [],
                'source': event.get('source', 'scraper'),
                'last_scraped': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Başlık yoksa atla
            if not event_data['title'] or len(event_data['title']) < 3:
                continue
            
            # Aynı başlık ve tarih varsa güncelle, yoksa ekle
            existing = events_collection.find_one({
                'title': event_data['title'],
                'date': event_data['date']
            })
            
            if existing:
                events_collection.update_one(
                    {'_id': existing['_id']},
                    {'$set': event_data}
                )
                updated_count += 1
            else:
                event_data['created_at'] = datetime.now()
                events_collection.insert_one(event_data)
                saved_count += 1
        
        except Exception as e:
            logger.error(f"Etkinlik kaydetme hatası: {e}")
            continue
    
    logger.info(f"✅ {saved_count} yeni etkinlik eklendi, {updated_count} etkinlik güncellendi")
    return saved_count, updated_count

def clean_old_events():
    """Geçmiş tarihlerdeki etkinlikleri temizler"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    result = events_collection.delete_many({'date': {'$lt': yesterday}})
    
    logger.info(f"🗑️ {result.deleted_count} eski etkinlik silindi")
    return result.deleted_count

# ============ MAIN SCRAPER FUNCTION ============

def run_scraper():
    """Ana scraper fonksiyonu - Sadece Antalya için"""
    logger.info("=" * 50)
    logger.info("🚀 Antalya Event Scraper Başlatıldı")
    logger.info("=" * 50)
    
    start_time = time.time()
    all_events = []
    
    # Biletinial'den çek
    try:
        biletinial_events = scrape_biletinial()
        all_events.extend(biletinial_events)
    except Exception as e:
        logger.error(f"Biletinial scraping hatası: {e}")
    
    # BUBilet'ten çek
    try:
        bubilet_events = scrape_bubilet()
        all_events.extend(bubilet_events)
    except Exception as e:
        logger.error(f"BUBilet scraping hatası: {e}")
    
    # Biletix'ten çek
    try:
        biletix_events = scrape_biletix()
        all_events.extend(biletix_events)
    except Exception as e:
        logger.error(f"Biletix scraping hatası: {e}")
    
    # Veritabanına kaydet
    if all_events:
        saved, updated = process_and_save_events(all_events)
    else:
        logger.warning("⚠️ Hiç etkinlik bulunamadı!")
        saved, updated = 0, 0
    
    # Eski etkinlikleri temizle
    deleted = clean_old_events()
    
    # Özet
    elapsed_time = time.time() - start_time
    logger.info("=" * 50)
    logger.info(f"✅ Scraper tamamlandı - Süre: {elapsed_time:.2f} saniye")
    logger.info(f"📊 Toplam: {len(all_events)} etkinlik toplandı")
    logger.info(f"➕ Yeni: {saved} | 🔄 Güncellenen: {updated} | 🗑️ Silinen: {deleted}")
    logger.info(f"📅 Veritabanında toplam: {events_collection.count_documents({})} etkinlik")
    logger.info("=" * 50)
    
    return {
        'success': True,
        'total_scraped': len(all_events),
        'saved': saved,
        'updated': updated,
        'deleted': deleted,
        'duration': elapsed_time
    }

if __name__ == '__main__':
    try:
        result = run_scraper()
        exit(0 if result['success'] else 1)
    except Exception as e:
        logger.error(f"❌ Kritik hata: {e}")
        import traceback
        logger.error(traceback.format_exc())
        exit(1)
