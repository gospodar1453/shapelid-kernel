# Shapelid Geometry Kernel — Sürüm Notları

Bu belge, Shapelid fiyatlandırma motorunun tüm önemli değişikliklerini kronolojik sırayla listeler.  
Versiyon şeması: **MAJOR.MINOR.PATCH** — Railway üzerinde otomatik deploy edilir.

---

## [2.1.0] — 2026-07-27

### 🎯 Özet
`finish_rates.py` modülü sıfırdan yeniden yazıldı.  
Tüm finish/color seçenekleri artık platform'un gerçek entity veritabanından (`MaterialFinish`, `MaterialColor`) türetilmektedir.

### ✨ Yeni Özellikler
- **43 finish seçeneği** — platform `MaterialFinish` entity'siyle birebir eşleşme:
  - Mekanik: `Bead Blast`, `Bead Blasting`, `Electropolishing`
  - Kaplama: `Nickel Plating`, `Electroless Nickel Plating`, `Gold Plating`, `Silver Plating`, `Electrolytic Zinc`
  - Kimyasal: `Zinc Coating / Galvanising`, `Chromate Conversion`, `Passivation`, `Passivate`, `Black Oxide`
  - Anodizing: `Anodising`, `Anodising Hardcoat`
  - Boya: `Powder Coating`, `Paint (RAL)`
  - Isı işlemi: `Annealing`, `Tempering`, `Through Hardening`, `Case Hardening`
  - Injection kalıp yüzeyi — SPI standartları: `SPI A-3`, `SPI B-2`, `SPI C-1`, `SPI C-2`, `SPI D-2`, `SPI D-3`
  - Injection kalıp dokusu — VDI 3400: `VDI-12`, `VDI-21`, `VDI-24`, `VDI-27`, `VDI-36`, `VDI-42`
  - 3D baskı özel: `Natural`, `Matte`, `Strip and Ship`, `Quick Clear`, `Media Blast`
- **20 renk seçeneği** — platform `MaterialColor` entity'siyle eşleşme:  
  `Black`, `White`, `Gray`, `Light Gray`, `Dark Gray`, `Red`, `Blue`, `Green`, `Yellow`, `Orange`, `Purple`, `Clear`, `Tan`, `Natural`, `Other` ve daha fazlası
- **`FINISH_ALIAS` + `COLOR_ALIAS`** tabloları: platform'dan gelen ham başlıklar (`"Bead Blasting"`, `"SPI A-3"` vb.) doğrudan `resolve_finish()` / `resolve_color()` fonksiyonlarına verilebilir
- **`INFILL_PRESETS`**: SpecOption'dan türetilen `UltraLight`, `Light`, `Standard`, `Solid`, `Full` seçenekleri
- **`_normalize()`** yardımcı fonksiyonu: bilinmeyen başlıkları otomatik key'e çevirir

### 🔧 Değişiklikler
- Eski sahte kodlar kaldırıldı: `vapor_smoothing`, `sandpaper_300`, `sandpaper_1000`, `anodize_clear`, `anodize_color`, `media_blast` (eski format)
- `resolve_finish()` artık platform `MaterialFinish.title` değerini direkt kabul ediyor (alias dönüşümü otomatik)
- `apply_options()` take_rate parametresi eklendi (default: `0.28`)
- `get_options_for_technology()` fonksiyonu `/options` endpoint'i için refactor edildi

### 🐛 Düzeltmeler
- Teknoloji uyumsuzluğunda fallback mantığı düzeltildi (uyumsuz finish → `standard`, uyarı ile)
- Resolution için SpecOption'dan gelen virgüllü string'ler (`"High, Standard"`) parse edildi

---

## [2.0.0] — 2026-07-26

### 🎯 Özet
Faz-2: Profesyonel üretim parametrelerinin fiyatlandırma motoruna entegrasyonu.

### ✨ Yeni Özellikler
- **`/options` endpoint**: `GET /options?technology={tech}` — frontend dropdown listelerini besler
- **Finish parametresi**: `standard`, `vapor_smoothing`, `bead_blast`, `powder_coating`, `nickel_plating`, `painting`, `passivation`, `electropolish`
- **Color parametresi**: `natural_grey`, `black_dyed`, `white_dyed`, `color_dyed`, `filament_color`, `resin_color`
- **Resolution parametresi**: FDM için `draft/standard/fine/ultra`, SLA için `sla_25/sla_50`, DMLS için `dmls_std/dmls_fine`
- **Hardness parametresi**: `shore_45a` → `shore_95a` (TPU/elastomer malzemeleri)
- **Tolerance parametresi**: `standard (±0.5mm)` → `ultra (±0.05mm)`
- **Certification parametresi**: `none`, `material_cert (+$8)`, `first_article (+$25)`, `iso_inspection (+$50)`
- **Infill preset string'leri**: `"sparse"`, `"standard"`, `"solid"`, `"full"` (önceden yalnızca float oranı destekleniyordu)
- **`pricing/finish_rates.py`** yeni modül oluşturuldu
- **`apply_options()`** fonksiyonu: `base_unit × Π(multipliers) + Σ(flat_costs) / (1 - take_rate)`

### 🔧 Değişiklikler
- `pricing/engine.py` v2.0.0'a yükseltildi — Faz-2 parametreleri entegre edildi
- `main.py` yeni query parametreleri eklendi: `finish`, `color`, `resolution`, `hardness`, `tolerance`, `certification`, `infill`
- `functions/kernelAnalyze.ts` (Client Portal) Faz-2 parametrelerini kernel'e iletecek şekilde güncellendi

### 🐛 Düzeltmeler
- GitHub reposu root'u ile Railway çalışma dizini hizalandı (path tutarsızlıkları giderildi)
- `main.py` ve `pricing/finish_rates.py` repo root'a taşındı

---

## [1.0.0] — 2026-07-10

### 🎯 Özet
İlk production deploy — Faz-1: STL bazlı geometrik analiz ve temel fiyatlandırma motoru.

### ✨ Özellikler
- **FastAPI** mikroservisi — Railway üzerinde Docker tabanlı deploy
- **`/analyze`** endpoint: STL/OBJ dosyası yükle → geometri analizi + anlık fiyat
- **`/analyze-dxf`** endpoint: DXF (2D lazer/büküm) dosyası analizi
- **Geometrik analiz**: `trimesh` + `numpy` ile hacim (cm³), yüzey alanı (cm²), boyutlar, watertight kontrolü
- **Fiyatlandırma motoru** (`pricing/engine.py`):
  - Teknoloji bazlı malzeme maliyeti (USD/kg × hacim × yoğunluk)
  - Makine/setup sabit giderleri (`pricing/machine_rates.py`)
  - Statik malzeme fallback (`pricing/material_rates.py`)
  - TCMB ForexBuying kuru + **%4 operasyonel buffer** (4 saatlik cache)
  - Teknoloji bazlı teklif geçerlilik süresi (`valid_until`)
- **DB entegrasyonu** (`pricing/db_prices.py`): `MaterialPrice` entity'sinden canlı fiyat çekme
  - `material_price_usd_per_kg` parametresi ile manuel override desteği
- **Desteklenen teknolojiler**: FDM, SLA, SLS, MJF, DMLS, Laser Cutting, Bending, CNC Machining
- **CORS** tam açık (Client Portal + Partner Portal entegrasyonu)

### 🏗 Altyapı
- Python 3.11 + Debian (trixie) Docker imajı
- Railway otomatik deploy (GitHub `main` branch push ile tetiklenir)
- Production URL: `https://shapelid-kernel-production.up.railway.app`

---

## Roadmap

| Faz | Kapsam | Durum |
|-----|--------|-------|
| Faz-1 | STL/DXF geometrik analiz, temel fiyatlandırma | ✅ Tamamlandı |
| Faz-2 | Finish/Color/Resolution/Hardness/Tolerance/Cert parametreleri | ✅ Tamamlandı |
| Faz-3 | SLS/MJF nesting optimizasyonu | 🔜 Planlandı |
| Faz-4 | SLA/DMLS destek yapısı analizi | 🔜 Planlandı |
| Faz-5 | CNC/EDM feature recognition (OpenCascade/OCCT) | 🔜 Planlandı |
| ML | Üretici geri bildiriminden fiyat kalibrasyon döngüsü | 🔜 Planlandı |
