# Shapelid Geometry Kernel

**Production:** `https://shapelid-kernel-production.up.railway.app`  
**Versiyon:** `2.1.0` — Faz-2.1 (Platform entegrasyonlu finish/color sistemi)  
**Platform:** Railway · Docker · FastAPI · Python 3.11

---

## Nedir?

Shapelid'in anlık üretim fiyatlandırma motorudur. Müşteri CAD dosyasını (STL/DXF) analiz eder, seçilen teknoloji ve parametrelere göre gerçek zamanlı fiyat hesaplar.

**Mimari:** `Manufacturer of Record (MoR)` modeli — müşteri ödemesi ile üretici ödemesi arasındaki take-rate fark üzerinden gelir elde edilir.

---

## Endpoints

### `GET /health`
Servis durumu, versiyon ve güncel kur bilgisi.

```json
{
  "status": "ok",
  "version": "2.1.0",
  "exchange_rate": { "usd_try": 47.16, "buffer_pct": 4.0 }
}
```

### `POST /analyze`
STL/OBJ dosyası geometrik analizi ve fiyatlandırma.

**Query parametreleri:**

| Parametre | Tip | Default | Açıklama |
|-----------|-----|---------|----------|
| `technology` | str | `fdm` | Üretim teknolojisi |
| `material` | str | `pla` | Malzeme adı |
| `quantity` | int | `1` | Adet |
| `infill` | float/str | `0.20` | Dolgu oranı (0-1) veya preset (`ultralight/light/standard/solid/full`) |
| `finish` | str | `standard` | Yüzey işlemi (platform title veya key) |
| `color` | str | `none` | Renk seçimi |
| `resolution` | str | `standard` | Çözünürlük/katman kalınlığı |
| `hardness` | str | `standard` | Shore sertliği (TPU için) |
| `tolerance` | str | `standard` | İşleme toleransı |
| `certification` | str | `none` | Kalite sertifikası |
| `material_price_usd_per_kg` | float | `None` | Manuel fiyat override |

**Desteklenen teknolojiler:**  
`fdm` · `sla` · `sls` · `mjf` · `dmls` · `laser` · `bending` · `cnc_machining` · `polyjet` · `injection` · `die_casting` · `vacuum_casting`

### `POST /analyze-dxf`
DXF dosyası analizi (Laser Cutting / Bending için 2D şekil).

### `GET /options?technology={tech}`
Belirli bir teknoloji için geçerli seçim listelerini döndürür.  
**Client Portal dropdown'larını beslemek için kullanılır.**

```json
{
  "technology": "cnc_machining",
  "finish": [
    { "key": "bead_blast", "label": "Bead Blast", "multiplier": 1.06, "flat_cost": 0.5 },
    { "key": "anodising_hardcoat", "label": "Anodising Hardcoat", "multiplier": 1.14, "flat_cost": 5.0 },
    ...
  ],
  "color": [...],
  "tolerance": [...],
  "certification": [...]
}
```

---

## Fiyatlandırma Modeli

```
unit_price_final = base_material_cost
                 × finish_multiplier
                 × color_multiplier
                 × resolution_multiplier
                 × hardness_multiplier
                 × tolerance_multiplier
                 + (flat_costs) / (1 - take_rate)
```

**Maliyet bileşenleri:**
- `base_material_cost` = `MaterialPrice` entity'sinden canlı USD/kg × hacim (cm³) × yoğunluk (g/cm³) / 1000
- `flat_costs` = finish + color + certification sabit giderleri (USD)
- Kur: TCMB ForexBuying + **%4 operasyonel buffer** (4 saatlik cache)

---

## Finish Sistemi (v2.1.0)

Tüm finish seçenekleri **platform `MaterialFinish` entity'siyle** birebir eşleşir.  
`resolve_finish(platform_title, technology)` fonksiyonu hem platform başlığını (`"Anodising Hardcoat"`) hem de key formatını (`"anodising_hardcoat"`) kabul eder.

**Teknoloji bazlı finish sayıları:**

| Teknoloji | Finish | Color | Resolution | Infill | Tolerance |
|-----------|--------|-------|------------|--------|-----------|
| FDM | 4 | 10 | 4 | 5 | — |
| SLA | 8 | 10 | 2 | — | — |
| SLS / MJF | 5 | 10 | 1 | — | — |
| DMLS | 13 | 10 | 2 | — | — |
| CNC Machining | 25 | 10 | — | — | 4 |
| Laser / Bending | 11 | 10 | — | — | — |
| Injection | 15 (SPI+VDI) | 10 | — | — | — |
| Polyjet | 5 | 10 | 2 | — | — |

---

## Proje Yapısı

```
shapelid-kernel/
├── main.py                    # FastAPI app — endpoints
├── Dockerfile                 # Railway deploy
├── requirements.txt
├── CHANGELOG.md               # Sürüm notları
├── analyzers/
│   ├── stl_analyzer.py        # trimesh/numpy STL analizi
│   └── dxf_analyzer.py        # ezdxf DXF analizi
└── pricing/
    ├── engine.py              # Fiyatlandırma çekirdeği (v2.0.0)
    ├── finish_rates.py        # Finish/Color/Resolution/Infill/Hardness/Tolerance (v2.1.0)
    ├── db_prices.py           # MaterialPrice entity'den canlı fiyat
    ├── exchange_rate.py       # TCMB kur + %4 buffer
    ├── machine_rates.py       # Makine/setup sabit giderleri
    └── material_rates.py      # Statik malzeme fallback fiyatları
```

---

## Deploy

Railway üzerinde `main` branch'e push ile otomatik deploy tetiklenir.

```bash
# Geliştirme
git push github main

# Local test
uvicorn main:app --reload --port 8000
```

**ÖNEMLİ:** Base44 S3 (`origin`) değil, **GitHub remote (`github`)** Railway'i tetikler.

---

## Versiyon Geçmişi

Detaylı sürüm notları için [CHANGELOG.md](CHANGELOG.md) dosyasına bakın.

| Versiyon | Tarih | Özet |
|----------|-------|------|
| 2.1.0 | 2026-07-27 | Platform gerçek finish/color değerleri (43 finish, 20 renk, SPI+VDI) |
| 2.0.0 | 2026-07-26 | Faz-2: finish/color/resolution/hardness/tolerance/cert parametreleri |
| 1.0.0 | 2026-07-10 | Faz-1: STL/DXF geometrik analiz, temel fiyatlandırma motoru |
