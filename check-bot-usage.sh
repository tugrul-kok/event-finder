#!/bin/bash

# Telegram Bot Kullanımını Kontrol Etme Scripti
# Sunucuda çalıştırın: bash check-bot-usage.sh

echo "🔍 Telegram Bot Kullanım Analizi"
echo "=================================="
echo ""

# Systemd service loglarından kullanıcı mesajlarını bul
echo "📱 Son Kullanıcı Mesajları (Systemd Logları):"
echo "----------------------------------------"
sudo journalctl -u events --no-pager | grep -E "User.*message:|User.*used.*command" | tail -50

echo ""
echo ""

# Kullanıcı isimlerini listele
echo "👥 Botu Kullanan Kullanıcılar:"
echo "----------------------------------------"
sudo journalctl -u events --no-pager | grep -E "User.*message:|User.*used.*command" | sed -E 's/.*User ([^(]+) \(ID: ([^,]+),.*/\1 (ID: \2)/' | sort | uniq -c | sort -rn

echo ""
echo ""

# Toplam mesaj sayısı
echo "📊 İstatistikler:"
echo "----------------------------------------"
TOTAL=$(sudo journalctl -u events --no-pager | grep -cE "User.*message:|User.*used.*command")
UNIQUE_USERS=$(sudo journalctl -u events --no-pager | grep -E "User.*message:|User.*used.*command" | sed -E 's/.*User ([^(]+) \(ID: ([^,]+),.*/\2/' | sort | uniq | wc -l)
echo "Toplam etkileşim sayısı: $TOTAL"
echo "Benzersiz kullanıcı sayısı: $UNIQUE_USERS"

echo ""
echo ""

# Son 24 saatteki kullanım
echo "⏰ Son 24 Saatteki Kullanım:"
echo "----------------------------------------"
sudo journalctl -u events --since "24 hours ago" --no-pager | grep -E "User.*message:|User.*used.*command" | tail -20

echo ""
echo ""

# Bugünkü kullanım
echo "📅 Bugünkü Kullanım:"
echo "----------------------------------------"
TODAY=$(sudo journalctl -u events --since "today" --no-pager | grep -cE "User.*message:|User.*used.*command")
echo "Bugün toplam etkileşim: $TODAY"

echo ""
echo ""

# RAG kullanımı
echo "🤖 RAG Sistemi Kullanımı:"
echo "----------------------------------------"
RAG_COUNT=$(sudo journalctl -u events --no-pager | grep -c "RAG response sent")
SIMPLE_COUNT=$(sudo journalctl -u events --no-pager | grep -c "Simple search response sent")
echo "RAG ile yanıt verilen: $RAG_COUNT"
echo "Basit arama ile yanıt verilen: $SIMPLE_COUNT"

echo ""
echo "=================================="
echo "✅ Analiz tamamlandı"
