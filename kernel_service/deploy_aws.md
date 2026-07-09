# AWS App Runner — Deploy Kılavuzu

## Ön Gereksinimler
- AWS hesabı (aws.amazon.com)
- GitHub hesabı
- AWS CLI (opsiyonel, konsol üzerinden de yapılabilir)

---

## Adım 1: GitHub Repo Oluştur

1. github.com → "New repository"
2. İsim: `shapelid-kernel`
3. Private seç
4. `kernel_service/` klasörünün içeriğini bu repoya yükle:
   - `main.py`
   - `analyzers/` (klasör)
   - `pricing/` (klasör)
   - `requirements.txt`
   - `Dockerfile`
   - `apprunner.yaml`

```bash
git init
git add .
git commit -m "Kernel Faz-1 başlangıç"
git remote add origin https://github.com/SENIN_KULLANICI_ADIN/shapelid-kernel.git
git push -u origin main
```

---

## Adım 2: AWS App Runner Servisi Oluştur

1. AWS Konsolu → App Runner → "Create service"
2. **Source:** GitHub repository
3. **Connect to GitHub:** hesabını bağla, `shapelid-kernel` reposunu seç
4. **Branch:** main
5. **Deployment trigger:** Automatic (her push'ta otomatik deploy)

### Konfigürasyon
| Alan | Değer |
|---|---|
| Configuration file | Use configuration file (`apprunner.yaml`) |
| Instance size | 1 vCPU / 2 GB RAM |
| Auto scaling | Min 1, Max 5 instance |
| Health check path | `/health` |
| Region | eu-central-1 (Frankfurt) |

6. **Create & deploy** — ilk deploy ~5 dakika sürer

---

## Adım 3: Servis URL'ini Al

Deploy tamamlanınca App Runner sana şu formatta bir URL verir:
```
https://XXXXX.eu-central-1.awsapprunner.com
```

Bu URL'i kopyala — Base44 backend function'a ekleyeceğiz.

---

## Adım 4: Ortam Değişkenleri (Opsiyonel Güvenlik)

App Runner → Configuration → Environment variables:
```
API_KEY = shapelid_kernel_xxxx  # istersen basit API key auth ekle
```

---

## Tahmini Maliyet (eu-central-1, 2026 fiyatları)

| Kullanım | Maliyet/ay |
|---|---|
| 0-1M istek (ilk yıl free tier) | ~$0 |
| 1 vCPU aktif süre (720 saat) | ~$30 |
| Bekleme süresi (paused) | ~$5 |
| **Tipik MVP maliyeti** | **~$10-35/ay** |

Trafik artınca auto-scaling devreye girer, instance başına aynı maliyet.

---

## Güvenlik Notu

App Runner URL'i herkese açık. Base44 backend function'ı bu servisi çağırırken:
1. Basit API key header ekle: `X-Kernel-Key: shapelid_kernel_xxx`
2. App Runner'da bu key'i environment variable olarak tut
3. `main.py`'ye middleware ekleriz (istersen)
