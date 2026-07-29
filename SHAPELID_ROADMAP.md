# SHAPELID — STRATEJIK YOL HARITASI
## 29 Temmuz 2026

---

## 1. PAZAR DURUMU

### Rakip Analizi
| Platform | Durum | Model | Komisyon |
|----------|-------|-------|----------|
| Xometry (TR/Global) | Aktif — Tridi'yi satın aldı | MoR | %25-40 take rate |
| Hubs (Protolabs) | Aktif | MoR | %25-30 |
| Protolabs | Aktif | Hibrit (in-house + network) | %50-60 in-house, %25-30 network |
| Parkurda (Tezmaksan) | Aktif (TR) | SaaS/Abonelik | Listing fee |
| infoTRON | Aktif (TR) | Atolye | N/A |
| Shapeways | iflas (2024) | — | — |

### Kritik Bulgu
**Xometry 2023'te Tridi'yi satin aldi** -> Turkiye'de Xometry Turkiye olarak operate ediyor. Shapelid'in dogrudan rakibi Xometry Turkiye.

### Shapelid'in Avantajlari (Moat)
1. ML Kalibrasyon (Faz-7) — rakiplerde yok
2. 3D koordinat bazli yorum/collaboration
3. Multi-part nesting engine (Faz-6)
4. 4.124 uretici veritabani (yerel ag)

### Eksiklikler
1. Gorsel DfM feedback (3D viewer'da wall-thickness heatmap)
2. Otomatik mesh tamir
3. Enterprise SLA & lojistik routing
4. Siparis akisi & odeme
5. e-Fatura entegrasyonu

---

## 2. GELIR MODELI

### Onerilen Model: Hibrit MoR + Abonelik

#### A) Dinamik Komisyon (MoR)
Tek tip %28 yerine teknolojiye gore dinamik marj:
- FDM/SLA (Simple Mode): %35 — dusuk maliyet, yuksek hacim
- SLS/MJF/Polyjet/DMLS: %28-30 — endustriyel additive
- CNC Milling/Turning: %20 — fiyat hassasiyeti yuksek
- EDM/Laser Cutting/Bending: %18 — yuksek hacim, dusuk value-add

#### B) Uretici Abonelik Katmanlari
| Tier | Fiyat (TRY/ay) | Odeme Suresi | Ozellikler |
|------|---------------|-------------|-----------|
| Free | 0 | Net-45 | FDM/SLA, max 3 es zamanli is |
| Pro | 2.500 | Net-15 | Tum teknolojiler, max 15 is |
| Enterprise | 12.000 | Next-Day | API, ozel hesap yoneticisi |

#### C) Musteri Abonelik Katmanlari
| Tier | Fiyat (TRY/ay) | Ozellikler |
|------|---------------|-----------|
| Free | 0 | Pay-as-you-go, kredi karti |
| Pro (R&D) | 5.000 | Net-30 fatura, %5 rebate, oncelikli kuyruk |
| Enterprise | 20.000 | Net-45/60, %10 rebate, API, ozel QA |

#### D) Ek Gelir Akislari
1. QA & Sertifikasyon ucretleri (CoC, MTR, CMM raporu)
2. FastPay — ureticiye 3 gunde odeme, %3.5 factoring fee
3. DfM konsultasyon ucreti
4. Export arbitraj — Avrupa'ya EUR fiyatla, Turkiye'de uret (%45-55 take rate)

### 12 Aylik Gelir Projeksiyonu
| Senaryo | GMV (TRY) | Toplam Gelir (TRY) | Toplam Gelir (USD) |
|---------|-----------|-------------------|-------------------|
| Muhafazakar | 35.5M | 10.3M | $219K |
| Moderat | 114.8M | 35.9M | $762K |
| Agresif | 283.6M | 96.2M | $2.04M |

### Turkiye Ozellikleri
- PayTR Marketplace → split payment (TCMB uyumlu)
- Taksit secenekleri (3-12 ay)
- e-Fatura zorunlu (GIB)
- KDV %20 (MoR modelinde sadece marj uzerinden)
- USD cinsinden fiyat + TCMB kur + %4 buffer + 24 saat gecerlilik

---

## 3. KULLANICI OZELLIKLERI — ONCELIK SIRASI

### FAZ 1: TEMEL (Odeme & Veritabani)
Musteri:
- Cok parcali sepet & checkout
- PayTR entegrasyonu (kurumsal KK + taksit + EFT)
- e-Fatura otomasyon (GIB VKN sorgulama)
- MoR garanti kapsami

Uretici:
- Partner Portal & Job Board
- Otomatik uretim paketi (CAD + teknik spec + kargo etiketi)
- E-Fatura akisi (uretici -> Shapelid)

Admin:
- Onboarding CRM (4.124 lead -> aktif partner)
- Onay/Red paneli

Veritabani ihtiyaclari: Orders, Payments, Shipments, SupplierProfiles entity'leri

### FAZ 2: FULFILLMENT & YONLENDIRME
- Partner Portal job board (kapasite bazli yonlendirme)
- Lojistik API (Yurtici/Kolay Gelsin/UPS)
- QC konsolu (merkezi Istanbul + self-QC mobil)
- Uretici dogrulama pipeline (5 asamali)

### FAZ 3: GUVEN & NAKIT AKISI
- Interaktif DfM (3D viewer'da wall-thickness heatmap)
- FastPay (3 gunde odeme, %3.5 fee)
- Partner Success Score (0-100, OTD + kalite)
- Resmi PDF teklif generator (kase/imza)
- WhatsApp is bildirim botu

### FAZ 4: ENTERPRISE
- STEP/IGES parser (CNC tolerans pricing icin kritik)
- AI Design-to-Cost (tolerans/malzeme degisimi -> tasarruf onerisi)
- Export portal (EUR fiyat, Avrupa musteri)
- Carbon footprint hesabi (Scope 3)
- ERP/CAD API entegrasyonu

---

## 4. UYGULAMA SIRASI

[Simdi] -> Faz 1: Odeme + e-Fatura + Siparis akisi + Partner Portal temel
[+2 ay] -> Faz 2: Job Board + Lojistik + QC + Uretici onboarding
[+4 ay] -> Faz 3: DfM + FastPay + PSS + PDF Teklif + WhatsApp bot
[+6 ay] -> Faz 4: STEP/IGES + AI DTC + Export + Carbon + Enterprise API

### Teknik On Kosullar
1. PayTR Marketplace sub-merchant kaydi (4.124 lead icin)
2. e-Fatura entegrasyonu (Parasut/BizimHesap)
3. Orders/Payments/Shipments entity'leri olusturulmali
4. STEP/IGES parser (CNC fiyatlandirma icin kritik — STL yetersiz)

---

## 5. HEMEN BASLANMASI GEREKENLER
1. PayTR Marketplace basvurusu
2. e-Fatura API entegrasyonu (Parasut)
3. Orders ve Payments entity'leri
4. Client Portal -> clone -> Partner Portal
5. Dinamik komisyon matrisi kernel'a entegrasyon
