# GitHub Actions ile Otomatik Deployment

Bu proje GitHub Actions kullanarak otomatik deployment yapılandırması içerir.

## 🚀 Kurulum

### 1. GitHub Secrets Ayarlama

GitHub repository'nizde şu secrets'ları ekleyin:

**Settings → Secrets and variables → Actions → New repository secret**

#### Gerekli Secrets:

1. **`SSH_PRIVATE_KEY`**
   - Sunucuya SSH ile bağlanmak için private key
   - `~/.ssh/id_rsa` dosyasının içeriği (tam içerik, başında `-----BEGIN` ve sonunda `-----END` dahil)

2. **`SERVER_HOST`**
   - Sunucu IP adresi veya domain
   - Örnek: `65.21.182.26` veya `events.tugrul.app`

3. **`SERVER_USER`**
   - SSH kullanıcı adı
   - Örnek: `root` veya `ubuntu`

### 2. SSH Key Oluşturma (Eğer yoksa)

Sunucuda:

```bash
# Sunucuda SSH key oluştur (eğer yoksa)
ssh-keygen -t rsa -b 4096 -C "github-actions"

# Public key'i authorized_keys'e ekle
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Local'de private key'i kopyala:

```bash
# Local'de private key'i göster
cat ~/.ssh/id_rsa

# Bu içeriği GitHub Secrets → SSH_PRIVATE_KEY olarak ekle
```

### 3. İki Deployment Yöntemi

Projede iki farklı deployment workflow'u var:

#### Yöntem 1: Git Pull (Önerilen)

**Dosya:** `.github/workflows/deploy.yml`

**Gereksinimler:**
- Sunucuda `/var/www/events` dizininde git repo clone edilmiş olmalı

**Kurulum:**

```bash
# Sunucuda
cd /var/www/events
git remote add origin https://github.com/tugrul-kok/event-finder.git
git pull origin main
```

**Avantajlar:**
- ✅ Hızlı (sadece git pull)
- ✅ Git history korunur
- ✅ Daha az dosya transferi

#### Yöntem 2: SCP ile Dosya Kopyalama

**Dosya:** `.github/workflows/deploy-with-scp.yml`

**Gereksinimler:**
- Sadece SSH erişimi yeterli

**Avantajlar:**
- ✅ Git gerekmez
- ✅ Tüm dosyalar kopyalanır
- ✅ Daha güvenli (sadece gerekli dosyalar)

**Kullanım:**

Workflow dosyasını `.github/workflows/deploy.yml` olarak yeniden adlandırın:

```bash
mv .github/workflows/deploy-with-scp.yml .github/workflows/deploy.yml
```

## 📋 Workflow Özellikleri

### Otomatik Tetikleme

- **Push to main**: `main` branch'ine push yapıldığında otomatik çalışır
- **Manuel tetikleme**: GitHub Actions tab'ından manuel çalıştırılabilir

### Deployment Adımları

1. ✅ Code checkout
2. ✅ SSH bağlantısı kurma
3. ✅ Dosyaları güncelleme (git pull veya SCP)
4. ✅ Python paketlerini güncelleme
5. ✅ Dosya izinlerini düzeltme
6. ✅ Servisi yeniden başlatma
7. ✅ Health check
8. ✅ Deployment summary

### Güvenlik

- ✅ `.env` dosyası korunur (backup/restore)
- ✅ `venv` dizini korunur
- ✅ SSH key GitHub Secrets'da güvenli saklanır

## 🔧 Kullanım

### Otomatik Deployment

Sadece `main` branch'ine push yapın:

```bash
git add .
git commit -m "Update features"
git push origin main
```

GitHub Actions otomatik olarak deployment'ı başlatacak.

### Manuel Deployment

1. GitHub repository → **Actions** tab
2. **Deploy to Server** workflow'unu seç
3. **Run workflow** butonuna tıkla
4. Branch seç (genellikle `main`)
5. **Run workflow** butonuna tıkla

### Deployment Logları

GitHub Actions tab'ından deployment loglarını görebilirsiniz:

- ✅ Başarılı deployment: Yeşil checkmark
- ❌ Başarısız deployment: Kırmızı X
- 📋 Detaylı loglar: Her step'in loglarını görebilirsiniz

## 🐛 Sorun Giderme

### SSH Bağlantı Hatası

**Hata:** `Permission denied (publickey)`

**Çözüm:**
1. SSH_PRIVATE_KEY secret'ının doğru olduğundan emin olun
2. Private key'in başında `-----BEGIN` ve sonunda `-----END` olduğundan emin olun
3. Sunucuda `authorized_keys` dosyasını kontrol edin

### Servis Restart Hatası

**Hata:** `Failed to restart events.service`

**Çözüm:**
1. Sunucuda manuel kontrol:
   ```bash
   sudo systemctl status events
   sudo journalctl -u events -f
   ```

2. Dosya izinlerini kontrol:
   ```bash
   sudo chown -R www-data:www-data /var/www/events
   ```

### Health Check Hatası

**Hata:** `Health check failed`

**Çözüm:**
1. Servisin başlaması için biraz bekleyin (5-10 saniye)
2. Manuel kontrol:
   ```bash
   curl http://localhost:5001/health
   ```

### Git Pull Hatası

**Hata:** `fatal: not a git repository`

**Çözüm:**
1. Sunucuda git repo'yu clone edin:
   ```bash
   cd /var/www/events
   git init
   git remote add origin https://github.com/tugrul-kok/event-finder.git
   git pull origin main
   ```

2. Veya SCP yöntemini kullanın (git gerekmez)

## 📝 Notlar

- `.env` dosyası deployment sırasında korunur
- `venv` dizini korunur (yeniden oluşturulmaz)
- `logs` dizini korunur
- Deployment sırasında servis kısa bir süre durur (restart sırasında)

## 🔄 İleri Seviye

### Deployment Öncesi Test

Workflow'a test adımları ekleyebilirsiniz:

```yaml
- name: Run tests
  run: |
    python -m pytest tests/
```

### Deployment Sonrası Bildirim

Slack, Discord veya email bildirimleri ekleyebilirsiniz:

```yaml
- name: Notify on success
  if: success()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Deployment successful!'
```

## ✅ Checklist

- [ ] GitHub Secrets eklendi (SSH_PRIVATE_KEY, SERVER_HOST, SERVER_USER)
- [ ] SSH key sunucuda authorized_keys'e eklendi
- [ ] Workflow dosyası seçildi (deploy.yml veya deploy-with-scp.yml)
- [ ] İlk deployment test edildi
- [ ] Health check çalışıyor
- [ ] Web arayüzü erişilebilir

---

**Hazır!** Artık her push'ta otomatik deployment yapılacak! 🚀

