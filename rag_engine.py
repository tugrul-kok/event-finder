"""
RAG Engine - Retrieval-Augmented Generation Motoru
Kullanıcı sorgusuna göre alakalı etkinlikleri bulup, Gemini AI ile yanıt üretir
Based on the original rotiva project
"""

import os
from dotenv import load_dotenv

# Cache dizini ayarla (www-data için)
CACHE_DIR = os.getenv('HF_HOME', '/var/www/.cache/huggingface')
os.environ['HF_HOME'] = CACHE_DIR
os.environ['TRANSFORMERS_CACHE'] = CACHE_DIR
os.makedirs(CACHE_DIR, exist_ok=True)
import google.generativeai as genai
import logging
from rag_retriever import FAISSRetriever

load_dotenv()
logger = logging.getLogger(__name__)


class RAGEngine:
    """
    RAG (Retrieval-Augmented Generation) pipeline
    FAISS vektor DB + Embeddings + Gemini AI = Akıllı etkinlik asistanı
    """
    
    def __init__(self, events):
        # 🗄️ FAISS + Embedding tabanlı arama motoru
        logger.info("🔄 FAISS Retriever başlatılıyor...")
        self.retriever = FAISSRetriever(events)
        
        # 🤖 Gemini AI istemcisi
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY bulunamadı, RAG engine sadece retrieval yapacak")
            self.model = None
        else:
            try:
                genai.configure(api_key=api_key)
                # Try gemini-2.5-flash first, fallback to gemini-pro
                try:
                    self.model = genai.GenerativeModel('gemini-2.5-flash')
                except:
                    try:
                        self.model = genai.GenerativeModel('gemini-pro')
                    except:
                        self.model = None
                if self.model:
                    logger.info("✅ Gemini AI configured for RAG")
            except Exception as e:
                logger.warning(f"Gemini AI configuration failed: {e}")
                self.model = None
        
        logger.info("✅ RAG Engine başlatıldı (FAISS + Embeddings + Gemini)")
    
    def answer_question(self, query, city_filter='antalya', top_k=5):
        """
        Kullanıcı sorusuna RAG tabanlı yanıt üret
        
        Args:
            query: Kullanıcının sorusu
            city_filter: Şehir filtresi (varsayılan: "antalya")
            top_k: Kaç etkinlik alınacak (varsayılan: 5)
        
        Returns:
            dict: {'answer': str, 'sources': list} - AI yanıtı ve kullanılan kaynaklar
        """
        try:
            # 1. RETRIEVAL: En alakalı etkinlikleri bul (FAISS + Embeddings ile semantik arama)
            results = self.retriever.retrieve(query, k=top_k, city_filter=city_filter)
            
            if not results:
                return {
                    'answer': '😔 Üzgünüm, Antalya için kriterlerine uygun etkinlik bulamadım. Farklı bir arama yapmak ister misin?',
                    'sources': []
                }
            
            # 2. CONTEXT OLUŞTURMA: Bulunan etkinlikleri metin formatına çevir
            context_text = "İlgili Etkinlikler:\n\n"
            for i, result in enumerate(results, 1):
                event = result['event']
                context_text += f"{i}. {event.get('title', 'Etkinlik')}\n"
                if event.get('date'):
                    context_text += f"   Tarih: {event['date']}\n"
                if event.get('venue'):
                    context_text += f"   Yer: {event['venue']}\n"
                if event.get('city'):
                    context_text += f"   Şehir: {event['city']}\n"
                if event.get('url'):
                    context_text += f"   Link: {event['url']}\n"
                if event.get('price'):
                    context_text += f"   Fiyat: {event['price']}\n"
                if event.get('description'):
                    context_text += f"   Açıklama: {event['description'][:100]}...\n"
                context_text += "\n"
            
            # 3. GENERATION: Gemini AI ile doğal dil yanıtı üret
            if self.model:
                try:
                    prompt = f"""Sen Antalya Etkinlik Botu'sun, Antalya'daki etkinliklerin uzmanı bir asistansın.
Doğal, samimi ve yardımsever bir Türkçe konuşma tarzın var.

Kullanıcının sorusuna aşağıdaki etkinlik bilgilerine dayanarak yanıt ver:

{context_text}

Kullanıcı Sorusu: {query}

Yanıt Kuralları:
- Doğal, samimi ve yardımsever ol
- Emoji kullan (🎭🎵🎬🎨)
- Her etkinlik yeni satırda
- Etkinlik adını [Etkinlik İsmi](link) formatında markdown link yap (eğer link varsa)
- Tarih, yer ve fiyat bilgilerini paylaş
- Kullanıcıya soru sor (ilgi alanlarını keşfet)
- Antalya'ya özel odaklan

Yanıt:"""
                    
                    response = self.model.generate_content(prompt)
                    answer = response.text.strip()
                except Exception as e:
                    logger.error(f"Gemini generation error: {e}")
                    # Fallback to simple format
                    answer = self._format_simple_response(results)
            else:
                # Fallback to simple format if Gemini not available
                answer = self._format_simple_response(results)
            
            return {
                'answer': answer,
                'sources': [r['event'] for r in results]
            }
            
        except Exception as e:
            logger.error(f"RAG engine error: {e}")
            return {
                'answer': f"⚠️ Üzgünüm, bir hata oluştu. Lütfen tekrar dener misin?",
                'sources': []
            }
    
    def _format_simple_response(self, results):
        """Simple response formatting when Gemini is not available"""
        if not results:
            return "😔 Üzgünüm, etkinlik bulamadım."
        
        response = "🎉 Antalya'da bulduğum etkinlikler:\n\n"
        for i, result in enumerate(results, 1):
            event = result['event']
            title = event.get('title', 'Etkinlik')
            url = event.get('url', '')
            
            if url:
                response += f"{i}. [{title}]({url})\n"
            else:
                response += f"{i}. {title}\n"
            
            if event.get('date'):
                response += f"   📅 {event['date']}\n"
            if event.get('venue'):
                response += f"   📍 {event['venue']}\n"
            if event.get('price'):
                response += f"   💰 {event['price']}\n"
            response += "\n"
        
        response += "💡 Başka ne aramak istersin?"
        return response

