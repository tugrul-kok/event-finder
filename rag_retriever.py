"""
FAISS + Embedding Retriever - Kullanıcı sorgusuna göre en alakalı etkinlikleri bulur
Based on the original rotiva project
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FAISSRetriever:
    """
    FAISS vektor database + Sentence-Transformers embedding modeli ile semantik arama
    
    ✅ Embedding Model: paraphrase-multilingual-MiniLM-L12-v2 (Türkçe desteği)
    ✅ Vektor Database: FAISS (Facebook AI Similarity Search)
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
        
        logger.info(f"🔄 Embedding model yükleniyor: {model_name}")
        # 🤖 Embedding Model yükle (ilk seferde ~120MB indirecek)
        self.model = SentenceTransformer(model_name)
        logger.info(f"✅ Embedding model hazır (boyut: {self.model.get_sentence_embedding_dimension()})")
        
        # Her etkinlik için aranabilir metin oluştur
        self.texts = []
        for e in self.events:
            # Create searchable text from event fields
            searchable_text = f"{e.get('title', '')} {e.get('description', '')} {e.get('city', '')} {e.get('category', '')} {e.get('venue', '')}"
            self.texts.append(searchable_text)
        
        # 📊 Tüm etkinlikleri embedding'e çevir (vektör temsili)
        logger.info(f"🔄 {len(self.events)} etkinlik vektörlere dönüştürülüyor...")
        self.embeddings = self.model.encode(self.texts, show_progress_bar=False)
        
        # 🗄️ FAISS vektor database oluştur (hızlı benzerlik araması için)
        dimension = self.embeddings.shape[1]  # Vektör boyutu (384)
        self.index = faiss.IndexFlatL2(dimension)  # L2 mesafe metriği
        self.index.add(self.embeddings.astype('float32'))  # Vektörleri FAISS'e ekle
        
        logger.info(f"✅ FAISS Retriever hazır: {len(self.events)} etkinlik indekslendi")
    
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

