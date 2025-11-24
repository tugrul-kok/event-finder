"""
FAISS + Embedding Retriever - Kullanıcı sorgusuna göre en alakalı etkinlikleri bulur
Based on the original rotiva project

RAM Optimizasyonu:
- Model singleton pattern ile paylaşılıyor (her process'te bir kez yükleniyor)
- Model cache mekanizması (disk cache)
- Lazy loading (sadece gerektiğinde yükleniyor)
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging
import os
import threading

logger = logging.getLogger(__name__)

# Global model cache (process-level singleton)
_model_cache = {}
_model_lock = threading.Lock()


def _get_or_load_model(model_name, cache_dir=None):
    """
    Model'i singleton pattern ile yükle (process-level cache)
    Her process'te sadece bir kez yüklenir, thread-safe
    """
    global _model_cache, _model_lock
    
    with _model_lock:
        if model_name not in _model_cache:
            logger.info(f"🔄 Embedding model yükleniyor: {model_name} (ilk yükleme, cache'e alınıyor)")
            
            # Cache dizini ayarla
            if cache_dir is None:
                cache_dir = os.getenv('HF_HOME', os.path.join(os.path.expanduser('~'), '.cache', 'huggingface'))
            
            # Model'i cache dizininden yükle (disk cache kullan)
            try:
                # Model cache mekanizması - disk'ten yükle
                model = SentenceTransformer(
                    model_name,
                    cache_folder=cache_dir,
                    device='cpu'  # CPU kullan (GPU yoksa)
                )
                logger.info(f"✅ Embedding model hazır (boyut: {model.get_sentence_embedding_dimension()}, cache: {cache_dir})")
                _model_cache[model_name] = model
            except Exception as e:
                logger.error(f"❌ Model yükleme hatası: {e}")
                raise
        
        return _model_cache[model_name]


class FAISSRetriever:
    """
    FAISS vektor database + Sentence-Transformers embedding modeli ile semantik arama
    
    ✅ Embedding Model: paraphrase-multilingual-MiniLM-L12-v2 (Türkçe desteği)
    ✅ Vektor Database: FAISS (Facebook AI Similarity Search)
    ✅ RAM Optimizasyonu: Model singleton pattern ile paylaşılıyor
    """
    
    def __init__(self, events, model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Args:
            events: Etkinlik listesi (MongoDB cursor veya list)
            model_name: Huggingface embedding model (varsayılan: çok dilli model)
        """
        # Convert MongoDB cursor to list if needed
        if hasattr(events, '__iter__') and not isinstance(events, (list, tuple)):
            self.events = list(events)
        else:
            self.events = events
        
        # Model'i singleton pattern ile yükle (process-level cache)
        cache_dir = os.getenv('HF_HOME', '/app/model_cache')
        self.model = _get_or_load_model(model_name, cache_dir=cache_dir)
        
        # Her etkinlik için aranabilir metin oluştur
        self.texts = []
        for e in self.events:
            # Create searchable text from event fields
            searchable_text = f"{e.get('title', '')} {e.get('description', '')} {e.get('city', '')} {e.get('category', '')} {e.get('venue', '')}"
            self.texts.append(searchable_text)
        
        # 📊 Tüm etkinlikleri embedding'e çevir (vektör temsili)
        # Batch processing ile bellek kullanımını optimize et
        logger.info(f"🔄 {len(self.events)} etkinlik vektörlere dönüştürülüyor...")
        
        # Batch size ile bellek kullanımını kontrol et (büyük listeler için)
        batch_size = 32  # Her seferde 32 etkinlik işle
        embeddings_list = []
        
        for i in range(0, len(self.texts), batch_size):
            batch_texts = self.texts[i:i+batch_size]
            batch_embeddings = self.model.encode(batch_texts, show_progress_bar=False, convert_to_numpy=True)
            embeddings_list.append(batch_embeddings)
        
        # Tüm batch'leri birleştir
        self.embeddings = np.vstack(embeddings_list).astype('float32')
        
        # 🗄️ FAISS vektor database oluştur (hızlı benzerlik araması için)
        dimension = self.embeddings.shape[1]  # Vektör boyutu (384)
        self.index = faiss.IndexFlatL2(dimension)  # L2 mesafe metriği
        self.index.add(self.embeddings)  # Vektörleri FAISS'e ekle
        
        logger.info(f"✅ FAISS Retriever hazır: {len(self.events)} etkinlik indekslendi (RAM optimized)")
    
    def retrieve(self, query, k=5, city_filter=None):
        """
        Kullanıcı sorgusuna en yakın etkinlikleri bul (semantik arama)
        
        Args:
            query: Kullanıcının arama sorgusu
            k: Kaç etkinlik döndürülecek (varsayılan: 5)
            city_filter: Şehir filtresi (örn: "antalya")
        
        Returns:
            list: Her biri {'event': dict, 'score': float} içeren liste (benzerlik skoruna göre sıralı)
        """
        try:
            # 🔍 Kullanıcı sorgusunu embedding'e çevir
            query_embedding = self.model.encode([query])[0].astype('float32')
            
            # 🗄️ FAISS ile en yakın vektörleri bul (k*2 al, filtreleme için)
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1),
                min(k * 2, len(self.events))
            )
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                event = self.events[idx]
                
                # Şehir filtresi varsa uygula
                if city_filter:
                    event_city = str(event.get('city', '')).lower()
                    if event_city != city_filter.lower():
                        continue
                
                # FAISS L2 mesafesini benzerlik skoruna çevir (0-1 arası)
                # Düşük mesafe = yüksek benzerlik
                similarity_score = 1 / (1 + float(dist))
                
                results.append({
                    'event': event,
                    'score': similarity_score
                })
                
                # Yeterli sonuç toplandıysa dur
                if len(results) >= k:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Retrieval hatası: {e}")
            return []

